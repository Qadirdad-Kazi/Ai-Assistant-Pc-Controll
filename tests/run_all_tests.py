import unittest
import os
import sys
import time
import json
from pathlib import Path

def run_all_tests():
    """Discover and run all tests in the tests directory."""
    print("=" * 60)
    print(" Wolf AI 2.0 - Unified Test Runner")
    print("=" * 60)
    
    # Add project root to sys.path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Setup test suite
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(Path(__file__).parent), pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    duration = end_time - start_time
    
    # Prepare results summary
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(duration, 2),
        "total_tests": result.testsRun,
        "successful": result.wasSuccessful(),
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "details": {
            "failures": [str(f[0]) for f in result.failures],
            "errors": [str(e[0]) for e in result.errors]
        }
    }
    
    # Save report
    report_path = project_root / "wolf_ai_test_report.json"
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=4)
    
    # Try to print summary using safe characters for Windows console
    print("\n" + "=" * 60)
    print(f" Test Summary:")
    print(f" Run Date:   {summary['timestamp']}")
    print(f" Duration:   {summary['duration_seconds']}s")
    print(f" Total:      {summary['total_tests']}")
    print(f" Success:    {'YES' if summary['successful'] else 'NO'}")
    print(f" Failures:   {summary['failures']}")
    print(f" Errors:     {summary['errors']}")
    print(f" Skipped:    {summary['skipped']}")
    print("=" * 60)
    print(f" Report saved to: {report_path}")
    
    return summary["successful"]

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
