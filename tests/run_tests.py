#!/usr/bin/env python3
"""
Simple Test Runner for Wolf AI 2.0
Runs all test suites and generates a basic report.
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime

def run_test_suite(suite_name, test_file):
    """Run a single test suite using pytest."""
    print(f"🧪 Running {suite_name} Test Suite...")
    print("=" * 50)
    
    start_time = time.time()
    
    # Run pytest with basic options
    cmd = [
        sys.executable, "-m", "pytest", 
        test_file,
        "-v",
        "--tb=short",
        "--no-header",
        "--no-summary"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        duration = time.time() - start_time
        
        # Parse output to get test results
        output_lines = result.stdout.strip().split('\n')
        passed = 0
        failed = 0
        total = 0
        
        # Look for the final test summary line
        for line in output_lines:
            if "passed" in line and "failed" in line:
                # Parse line like "12 passed, 2 warnings in 25.41s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        passed = int(parts[i-1])
                    elif part == "failed" and i > 0:
                        failed = int(parts[i-1])
                total = passed + failed
                break
        
        # If no summary found, count from individual test lines
        if total == 0:
            for line in output_lines:
                if "::" in line and "PASSED" in line:
                    passed += 1
                elif "::" in line and "FAILED" in line:
                    failed += 1
            total = passed + failed
        
        status = "PASSED" if failed == 0 else "FAILED"
        
        print(f"✅ {suite_name}: {status} ({total} tests, {duration:.2f}s)")
        
        # Print some output for debugging
        if failed > 0:
            print("❌ Failed tests:")
            for line in output_lines:
                if "FAILED" in line and "::" in line:
                    print(f"  - {line.strip()}")
        
        return {
            "suite_name": suite_name,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": 0,
            "duration": duration,
            "status": status,
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ {suite_name}: TIMEOUT (> 5 minutes)")
        return {
            "suite_name": suite_name,
            "total_tests": 0,
            "passed": 0,
            "failed": 1,
            "skipped": 0,
            "duration": 300,
            "status": "TIMEOUT",
            "exit_code": 1,
            "output": "",
            "errors": "Test suite timed out"
        }
    except Exception as e:
        print(f"❌ {suite_name}: ERROR - {e}")
        return {
            "suite_name": suite_name,
            "total_tests": 0,
            "passed": 0,
            "failed": 1,
            "skipped": 0,
            "duration": 0,
            "status": "ERROR",
            "exit_code": 1,
            "output": "",
            "errors": str(e)
        }

def main():
    """Main test runner."""
    print("🚀 Starting Wolf AI 2.0 Test Suite")
    print("=" * 80)
    
    # Define test suites
    test_suites = [
        ("Vision Agent", "tests/test_vision_agent.py"),
        ("Neural Sonic TTS", "tests/test_neural_sonic.py"),
        ("Memory Recall", "tests/test_memory_recall.py"),
        ("Deep Research", "tests/test_deep_research.py"),
        ("Bug Watcher", "tests/test_bug_watcher.py")
    ]
    
    # Run all test suites
    results = []
    start_time = time.time()
    
    for suite_name, test_file in test_suites:
        result = run_test_suite(suite_name, test_file)
        results.append(result)
        print()  # Add spacing between suites
    
    total_duration = time.time() - start_time
    
    # Generate summary
    total_tests = sum(r["total_tests"] for r in results)
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    total_skipped = sum(r["skipped"] for r in results)
    
    print("\n" + "=" * 80)
    print("🎯 Wolf AI 2.0 Test Summary")
    print("=" * 80)
    print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
    print(f"🧪 Total Tests: {total_tests}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"⏭️  Skipped: {total_skipped}")
    
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
    else:
        print(f"📈 Success Rate: 0.0%")
    
    print("\n📋 Test Suite Results:")
    for result in results:
        status_emoji = "✅" if result["status"] == "PASSED" else "❌"
        print(f"  {status_emoji} {result['suite_name']}: {result['status']} ({result['passed']}/{result['total_tests']})")
    
    # Save results to JSON
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total_duration": total_duration,
        "summary": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "success_rate": (total_passed / max(total_tests, 1)) * 100
        },
        "test_suites": results
    }
    
    report_file = "wolf_ai_test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📊 Test report saved to: {report_file}")
    
    # Generate HTML report
    html_file = "wolf_ai_test_report.html"
    generate_html_report(report_data, html_file)
    print(f"🌐 HTML report saved to: {html_file}")
    
    # Return appropriate exit code
    if total_failed > 0:
        print(f"\n❌ {total_failed} test(s) failed. Check the report for details.")
        return 1
    else:
        print(f"\n🎉 All tests passed!")
        return 0

def generate_html_report(report_data, html_file):
    """Generate an HTML test report."""
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wolf AI 2.0 Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .test-suites {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .suite {{
            border-bottom: 1px solid #eee;
            padding: 20px;
        }}
        .suite:last-child {{
            border-bottom: none;
        }}
        .suite-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .suite-name {{
            font-weight: bold;
            font-size: 1.2em;
        }}
        .suite-status {{
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
        }}
        .status-passed {{
            background-color: #28a745;
        }}
        .status-failed {{
            background-color: #dc3545;
        }}
        .status-timeout {{
            background-color: #ffc107;
            color: #333;
        }}
        .status-error {{
            background-color: #6c757d;
        }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background-color: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background-color: #28a745;
            transition: width 0.3s ease;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🐺 Wolf AI 2.0 Test Report</h1>
        <p>Generated on {report_data['timestamp']}</p>
    </div>
    
    <div class="summary">
        <div class="summary-card">
            <h3>Total Tests</h3>
            <div class="value">{report_data['summary']['total_tests']}</div>
        </div>
        <div class="summary-card">
            <h3>✅ Passed</h3>
            <div class="value">{report_data['summary']['passed']}</div>
        </div>
        <div class="summary-card">
            <h3>❌ Failed</h3>
            <div class="value">{report_data['summary']['failed']}</div>
        </div>
        <div class="summary-card">
            <h3>📈 Success Rate</h3>
            <div class="value">{report_data['summary']['success_rate']:.1f}%</div>
        </div>
    </div>
    
    <div class="test-suites">
        <h2>📋 Test Suite Results</h2>
"""
    
    for suite in report_data['test_suites']:
        status_class = f"status-{suite['status'].lower()}"
        success_rate = (suite['passed'] / max(suite['total_tests'], 1)) * 100
        
        html += f"""
        <div class="suite">
            <div class="suite-header">
                <div class="suite-name">{suite['suite_name']}</div>
                <div class="suite-status {status_class}">{suite['status']}</div>
            </div>
            <div>Tests: {suite['passed']}/{suite['total_tests']} passed</div>
            <div>Duration: {suite['duration']:.2f}s</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate}%"></div>
            </div>
        </div>
"""
    
    html += """
    </div>
    
    <div class="footer">
        <p>Generated by Wolf AI 2.0 Test Runner</p>
    </div>
</body>
</html>
"""
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
