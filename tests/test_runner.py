"""
System Integration Test Runner
Comprehensive test runner for Wolf AI 2.0 ultimate enhancement testing.
"""

import pytest
import asyncio
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """Comprehensive test runner for Wolf AI 2.0."""
    
    def __init__(self):
        self.results = {
            "start_time": None,
            "end_time": None,
            "total_duration": 0,
            "test_suites": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0
            },
            "system_info": self._get_system_info()
        }
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system information for test report."""
        import platform
        import psutil
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
            "disk_free": f"{psutil.disk_usage('.').free / (1024**3):.2f} GB"
        }
    
    async def run_test_suite(self, suite_name: str, test_file: str, markers: List[str] = None) -> Dict[str, Any]:
        """Run a specific test suite."""
        print(f"\n🧪 Running {suite_name} Test Suite...")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Build pytest command
            pytest_args = [
                test_file,
                "-v",
                "--tb=short",
                "-x"  # Stop on first failure for faster debugging
            ]
            
            # Add markers if specified
            if markers:
                for marker in markers:
                    pytest_args.extend(["-m", marker])
            try:
            # Try to use pytest-json-report if available, otherwise use basic exit code
            try:
                import pytest_json_report
                pytest_args.extend([
                    "--json-report",
                    "--json-report-file=/tmp/test_report.json"
                ])
                exit_code = pytest.main(pytest_args)
                
                # Load test results
                try:
                    with open("/tmp/test_report.json", "r") as f:
                        test_data = json.load(f)
                except FileNotFoundError:
                    test_data = {"summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0}}
                
            except ImportError:
                # Fallback to basic pytest without JSON reporting
                exit_code = pytest.main(pytest_args)
                # Create basic test data based on exit code
                if exit_code == 0:
                    test_data = {"summary": {"total": 1, "passed": 1, "failed": 0, "skipped": 0}}
                else:
                    test_data = {"summary": {"total": 1, "passed": 0, "failed": 1, "skipped": 0}}
            
            duration = time.time() - start_time
            
            suite_results = {
                "exit_code": exit_code,
                "duration": duration,
                "total_tests": test_data["summary"]["total"],
                "passed": test_data["summary"]["passed"],
                "failed": test_data["summary"]["failed"],
                "skipped": test_data["summary"]["skipped"],
                "success_rate": (test_data["summary"]["passed"] / max(test_data["summary"]["total"], 1)) * 100,
                "status": "PASSED" if exit_code == 0 else "FAILED",
                "markers": markers or []
            }
            
            print(f"✅ {suite_name}: {suite_results['status']} ({suite_results['total_tests']} tests, {suite_results['duration']:.2f}s)")
            
            return suite_results
            
        except Exception as e:
            print(f"❌ Error running {suite_name}: {e}")
            return {
                "exit_code": 1,
                "duration": time.time() - start_time,
                "total_tests": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "success_rate": 0,
                "status": "ERROR",
                "error": str(e),
                "markers": markers or []
            }
    
    async def run_all_tests(self, include_integration: bool = False, test_type: str = "all") -> Dict[str, Any]:
        """Run all test suites."""
        print("🚀 Starting Wolf AI 2.0 Ultimate Enhancement Test Suite")
        print("=" * 80)
        
        self.results["start_time"] = datetime.now().isoformat()
        
        # Define test suites with their markers
        test_suites = [
            ("Vision Agent", "tests/test_vision_agent.py", []),
            ("Neural Sonic TTS", "tests/test_neural_sonic.py", []),
            ("Memory Recall", "tests/test_memory_recall.py", []),
            ("Deep Research", "tests/test_deep_research.py", []),
            ("Bug Watcher", "tests/test_bug_watcher.py", [])
        ]
        
        if include_integration:
            test_suites.extend([
                ("Vision Integration", "tests/test_vision_agent.py::TestVisionIntegration", ["integration", "vision"]),
                ("TTS Integration", "tests/test_neural_sonic.py::TestNeuralSonicIntegration", ["integration", "tts"]),
                ("Memory Integration", "tests/test_memory_recall.py::TestMemoryRecallIntegration", ["integration", "memory"]),
                ("Research Integration", "tests/test_deep_research.py::TestDeepResearchIntegration", ["integration", "research"]),
                ("Bug Watcher Integration", "tests/test_bug_watcher.py::TestBugWatcherIntegration", ["integration", "bugwatcher"])
            ])
        
        # Filter by test type if specified
        if test_type != "all":
            marker_mapping = {
                "unit": ["unit"],
                "integration": ["integration"],
                "vision": ["vision"],
                "tts": ["tts"],
                "memory": ["memory"],
                "research": ["research"],
                "bugwatcher": ["bugwatcher"]
            }
            if test_type in marker_mapping:
                target_markers = marker_mapping[test_type]
                test_suites = [(name, file, [m for m in markers if m in target_markers]) 
                              for name, file, markers in test_suites 
                              if any(m in target_markers for m in markers)]
        
        # Run each test suite
        for suite_name, test_file, markers in test_suites:
            suite_results = await self.run_test_suite(suite_name, test_file, markers)
            self.results["test_suites"][suite_name] = suite_results
            
            # Update summary
            self.results["summary"]["total_tests"] += suite_results["total_tests"]
            self.results["summary"]["passed"] += suite_results["passed"]
            self.results["summary"]["failed"] += suite_results["failed"]
            self.results["summary"]["skipped"] += suite_results["skipped"]
        
        self.results["end_time"] = datetime.now().isoformat()
        
        # Calculate total duration
        start = datetime.fromisoformat(self.results["start_time"])
        end = datetime.fromisoformat(self.results["end_time"])
        self.results["total_duration"] = (end - start).total_seconds()
        
        return self.results
    
    def generate_report(self, output_file: str = "test_report.json") -> None:
        """Generate comprehensive test report."""
        report = {
            "wolf_ai_test_report": {
                "version": "2.0.1",
                "test_type": "Ultimate Enhancement Testing",
                "generated_at": datetime.now().isoformat(),
                "results": self.results,
                "performance_metrics": self._calculate_performance_metrics(),
                "coverage_analysis": self._analyze_coverage(),
                "recommendations": self._generate_recommendations(),
                "system_health": self._assess_system_health()
            }
        }
        
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        
        # Also generate HTML report
        html_file = output_file.replace('.json', '.html')
        self._generate_html_report(html_file, report)
        
        print(f"\n📊 Test report saved to: {output_file}")
        print(f"🌐 HTML report saved to: {html_file}")
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics from test results."""
        if not self.results["test_suites"]:
            return {}
        
        durations = [suite["duration"] for suite in self.results["test_suites"].values()]
        total_tests = self.results["summary"]["total_tests"]
        
        return {
            "total_duration": self.results["total_duration"],
            "average_suite_duration": sum(durations) / len(durations) if durations else 0,
            "slowest_suite": max(durations) if durations else 0,
            "fastest_suite": min(durations) if durations else 0,
            "tests_per_second": total_tests / max(self.results["total_duration"], 1),
            "suite_performance": {
                name: {
                    "duration": results["duration"],
                    "tests_per_second": results["total_tests"] / max(results["duration"], 1),
                    "efficiency": "high" if results["duration"] < 10 else "medium" if results["duration"] < 30 else "low"
                }
                for name, results in self.results["test_suites"].items()
            }
        }
    
    def _analyze_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage based on test results."""
        total_modules = len(self.results["test_suites"])
        passed_modules = sum(1 for suite in self.results["test_suites"].values() if suite["status"] == "PASSED")
        
        return {
            "module_coverage": (passed_modules / max(total_modules, 1)) * 100,
            "test_execution_coverage": (self.results["summary"]["passed"] / max(self.results["summary"]["total_tests"], 1)) * 100,
            "integration_coverage": "included" if any("integration" in str(suite).lower() for suite in self.results["test_suites"]) else "excluded",
            "module_status": {
                name: "covered" if results["status"] == "PASSED" else "failed"
                for name, results in self.results["test_suites"].items()
            }
        }
    
    def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health based on test results."""
        total_tests = self.results["summary"]["total_tests"]
        failed_tests = self.results["summary"]["failed"]
        skipped_tests = self.results["summary"]["skipped"]
        
        health_score = 100
        if total_tests > 0:
            health_score -= (failed_tests / total_tests) * 50  # Penalize failures
            health_score -= (skipped_tests / total_tests) * 20  # Minor penalty for skips
        
        health_status = "excellent" if health_score >= 90 else "good" if health_score >= 75 else "fair" if health_score >= 60 else "poor"
        
        return {
            "overall_score": round(health_score, 1),
            "status": health_status,
            "issues": self._identify_health_issues(),
            "ready_for_production": health_score >= 75
        }
    
    def _identify_health_issues(self) -> List[str]:
        """Identify specific health issues."""
        issues = []
        
        for suite_name, results in self.results["test_suites"].items():
            if results["status"] == "FAILED":
                issues.append(f"Critical: {suite_name} tests failing")
            elif results["success_rate"] < 80:
                issues.append(f"Warning: Low success rate in {suite_name}")
            elif results["duration"] > 60:
                issues.append(f"Performance: {suite_name} tests running slowly")
        
        if self.results["summary"]["skipped"] > self.results["summary"]["total_tests"] * 0.3:
            issues.append("Configuration: Many tests being skipped (missing dependencies)")
        
        return issues
    
    def _generate_html_report(self, html_file: str, report_data: Dict[str, Any]) -> None:
        """Generate HTML report for better visualization."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Wolf AI 2.0 Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #333; border-bottom: 2px solid #007acc; padding-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007acc; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .suite-results {{ margin: 20px 0; }}
        .suite {{ border: 1px solid #ddd; margin: 10px 0; border-radius: 5px; }}
        .suite-header {{ padding: 15px; background: #f8f9fa; font-weight: bold; }}
        .suite-details {{ padding: 15px; }}
        .status-passed {{ color: #28a745; }}
        .status-failed {{ color: #dc3545; }}
        .status-skipped {{ color: #ffc107; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #dc3545, #ffc107, #28a745); }}
        .recommendations {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐺 Wolf AI 2.0 Test Report</h1>
            <p>Generated on {report_data['wolf_ai_test_report']['generated_at']}</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-value">{self.results['summary']['total_tests']}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value status-passed">{self.results['summary']['passed']}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value status-failed">{self.results['summary']['failed']}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value status-skipped">{self.results['summary']['skipped']}</div>
                <div class="metric-label">Skipped</div>
            </div>
            <div class="metric">
                <div class="metric-value">{self.results['total_duration']:.1f}s</div>
                <div class="metric-label">Duration</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {(self.results['summary']['passed'] / max(self.results['summary']['total_tests'], 1)) * 100}%"></div>
        </div>
        
        <div class="suite-results">
            <h2>Test Suite Results</h2>
            {self._generate_suite_html()}
        </div>
        
        <div class="recommendations">
            <h2>📋 Recommendations</h2>
            <ul>
                {"".join(f"<li>{rec}</li>" for rec in self._generate_recommendations())}
            </ul>
        </div>
    </div>
</body>
</html>
        """
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
    
    def _generate_suite_html(self) -> str:
        """Generate HTML for test suite results."""
        html = ""
        for suite_name, results in self.results["test_suites"].items():
            status_class = f"status-{results['status'].lower()}"
            html += f"""
            <div class="suite">
                <div class="suite-header">
                    <span class="{status_class}">{suite_name}: {results['status']}</span>
                    <span style="float: right;">{results['duration']:.2f}s</span>
                </div>
                <div class="suite-details">
                    <p>Tests: {results['passed']}/{results['total_tests']} passed</p>
                    <p>Success Rate: {results['success_rate']:.1f}%</p>
                </div>
            </div>
            """
        return html
    
    async def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks for all modules."""
        print("🚀 Running Performance Benchmarks...")
        benchmark_results = {}
        
        # Benchmark each test suite
        for suite_name, test_file in [
            ("Vision Agent", "tests/test_vision_agent.py"),
            ("Neural Sonic TTS", "tests/test_neural_sonic.py"),
            ("Memory Recall", "tests/test_memory_recall.py"),
            ("Deep Research", "tests/test_deep_research.py"),
            ("Bug Watcher", "tests/test_bug_watcher.py")
        ]:
            print(f"  📊 Benchmarking {suite_name}...")
            
            # Run multiple iterations to get average performance
            iterations = 3
            durations = []
            
            for i in range(iterations):
                start_time = time.time()
                exit_code = pytest.main([test_file, "-x", "--tb=no"])
                duration = time.time() - start_time
                durations.append(duration)
                
                if i < iterations - 1:  # Small delay between iterations
                    await asyncio.sleep(1)
            
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            benchmark_results[suite_name] = {
                "average_duration": avg_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "iterations": iterations,
                "performance_score": "excellent" if avg_duration < 5 else "good" if avg_duration < 15 else "fair" if avg_duration < 30 else "poor"
            }
            
            print(f"    ⏱️  Avg: {avg_duration:.2f}s (Min: {min_duration:.2f}s, Max: {max_duration:.2f}s)")
        
        # Store benchmark results
        self.results["performance_benchmarks"] = benchmark_results
        
        print(f"✅ Performance benchmarks completed for {len(benchmark_results)} modules")
        return benchmark_results
    
    async def continuous_monitoring(self, interval: int = 300) -> None:
        """Run continuous monitoring mode."""
        print(f"🔄 Starting continuous monitoring (interval: {interval}s)...")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                print(f"\n🕐 Running health check at {datetime.now().strftime('%H:%M:%S')}")
                
                # Quick health check
                checks = await SystemHealthChecker.check_prerequisites()
                SystemHealthChecker.print_health_check(checks)
                
                # Run a subset of critical tests
                critical_suites = [
                    ("Vision Agent", "tests/test_vision_agent.py", ["unit"]),
                    ("Memory Recall", "tests/test_memory_recall.py", ["unit"])
                ]
                
                monitoring_results = {}
                for suite_name, test_file, markers in critical_suites:
                    print(f"  🔍 Checking {suite_name}...")
                    results = await self.run_test_suite(suite_name, test_file, markers)
                    monitoring_results[suite_name] = results
                    
                    if results["status"] == "FAILED":
                        print(f"    ❌ {suite_name} failed!")
                    else:
                        print(f"    ✅ {suite_name} healthy")
                
                # Store monitoring results
                if "continuous_monitoring" not in self.results:
                    self.results["continuous_monitoring"] = []
                
                self.results["continuous_monitoring"].append({
                    "timestamp": datetime.now().isoformat(),
                    "health_checks": checks,
                    "test_results": monitoring_results
                })
                
                print(f"⏳ Next check in {interval} seconds...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Continuous monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        for suite_name, results in self.results["test_suites"].items():
            if results["status"] == "FAILED":
                recommendations.append(f"🔧 Fix failing tests in {suite_name}")
            elif results["success_rate"] < 80:
                recommendations.append(f"⚠️ Improve test coverage in {suite_name}")
        
        if self.results["summary"]["failed"] > 0:
            recommendations.append("🐛 Debug and fix failing tests before production deployment")
        
        if self.results["summary"]["skipped"] > self.results["summary"]["total_tests"] * 0.3:
            recommendations.append("🔌 Install missing dependencies to enable skipped tests")
        
        # Performance recommendations
        if "performance_benchmarks" in self.results:
            for suite_name, benchmark in self.results["performance_benchmarks"].items():
                if benchmark["performance_score"] in ["fair", "poor"]:
                    recommendations.append(f"⚡ Optimize performance of {suite_name} tests")
        
        # Health recommendations
        if "system_health" in self.results:
            health = self.results["system_health"]
            if not health["ready_for_production"]:
                recommendations.append("🏥 Address system health issues before deployment")
        
        if not recommendations:
            recommendations.append("✅ All systems ready for production!")
        
        return recommendations
    
    def print_summary(self) -> None:
        """Print test summary to console."""
        print("\n" + "=" * 80)
        print("🎯 Wolf AI 2.0 Test Summary")
        print("=" * 80)
        
        print(f"⏱️  Total Duration: {self.results['total_duration']:.2f} seconds")
        print(f"🧪 Total Tests: {self.results['summary']['total_tests']}")
        print(f"✅ Passed: {self.results['summary']['passed']}")
        print(f"❌ Failed: {self.results['summary']['failed']}")
        print(f"⏭️  Skipped: {self.results['summary']['skipped']}")
        
        success_rate = (self.results['summary']['passed'] / max(self.results['summary']['total_tests'], 1)) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n📋 Test Suite Results:")
        for suite_name, results in self.results["test_suites"].items():
            status_emoji = "✅" if results["status"] == "PASSED" else "❌"
            print(f"  {status_emoji} {suite_name}: {results['status']} ({results['passed']}/{results['total_tests']})")
        
        print("\n" + "=" * 80)

class SystemHealthChecker:
    """Check system health before running tests."""
    
    @staticmethod
    async def check_prerequisites() -> Dict[str, bool]:
        """Check if all prerequisites are met."""
        checks = {}
        
        # Check Python version
        checks["python_version"] = sys.version_info >= (3, 10)
        
        # Check required packages
        try:
            import pytest
            checks["pytest"] = True
        except ImportError:
            checks["pytest"] = False
        
        try:
            import psutil
            checks["psutil"] = True
        except ImportError:
            checks["psutil"] = False
        
        # Check Ollama (optional but recommended)
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            checks["ollama"] = response.status_code == 200
        except:
            checks["ollama"] = False
        
        # Check OmniParser (optional)
        try:
            response = requests.get("http://localhost:8001/", timeout=5)
            checks["omni_parser"] = response.status_code == 200
        except:
            checks["omni_parser"] = False
        
        return checks
    
    @staticmethod
    def print_health_check(checks: Dict[str, bool]) -> None:
        """Print health check results."""
        print("🔍 System Health Check")
        print("-" * 40)
        
        for check_name, status in checks.items():
            emoji = "✅" if status else "❌"
            status_text = "OK" if status else "MISSING"
            print(f"{emoji} {check_name.replace('_', ' ').title()}: {status_text}")
        
        print()

async def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="Wolf AI 2.0 Test Runner")
    parser.add_argument("--integration", action="store_true", help="Include integration tests")
    parser.add_argument("--suite", choices=["vision", "tts", "memory", "research", "bugwatcher"], 
                       help="Run specific test suite")
    parser.add_argument("--type", choices=["all", "unit", "integration", "vision", "tts", "memory", "research", "bugwatcher"],
                       default="all", help="Filter tests by type")
    parser.add_argument("--report", default="wolf_ai_test_report.json", 
                       help="Output report file")
    parser.add_argument("--skip-health", action="store_true", help="Skip system health check")
    parser.add_argument("--performance", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--continuous", action="store_true", help="Run in continuous monitoring mode")
    
    args = parser.parse_args()
    
    # Health check
    if not args.skip_health:
        checks = await SystemHealthChecker.check_prerequisites()
        SystemHealthChecker.print_health_check(checks)
        
        if not checks["python_version"]:
            print("❌ Python 3.10+ required. Current version:", sys.version)
            return
        
        if not checks["pytest"]:
            print("❌ pytest not installed. Run: pip install pytest")
            return
    
    # Run tests
    runner = TestRunner()
    
    if args.suite:
        # Run specific suite
        suite_mapping = {
            "vision": ("Vision Agent", "tests/test_vision_agent.py", []),
            "tts": ("Neural Sonic TTS", "tests/test_neural_sonic.py", []),
            "memory": ("Memory Recall", "tests/test_memory_recall.py", []),
            "research": ("Deep Research", "tests/test_deep_research.py", []),
            "bugwatcher": ("Bug Watcher", "tests/test_bug_watcher.py", [])
        }
        
        suite_name, test_file, markers = suite_mapping[args.suite]
        results = await runner.run_test_suite(suite_name, test_file, markers)
        runner.results["test_suites"][suite_name] = results
    else:
        # Run all tests
        await runner.run_all_tests(include_integration=args.integration, test_type=args.type)
    
    # Print summary and generate report
    runner.print_summary()
    runner.generate_report(args.report)
    
    # Performance benchmarks if requested
    if args.performance:
        print("\n🚀 Running Performance Benchmarks...")
        await runner.run_performance_benchmarks()
    
    # Continuous monitoring mode
    if args.continuous:
        print("\n🔄 Starting Continuous Monitoring Mode...")
        await runner.continuous_monitoring()
    
    # Exit with appropriate code
    total_failed = runner.results["summary"]["failed"]
    if total_failed > 0:
        print(f"\n❌ {total_failed} test(s) failed. Check the report for details.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed! Wolf AI 2.0 is ready for deployment.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
