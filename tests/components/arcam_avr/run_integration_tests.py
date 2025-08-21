#!/usr/bin/env python3
"""Integration test runner for Arcam AVR component."""
import asyncio
import sys
import time
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest


def main():
    """Run integration tests with various configurations."""
    parser = argparse.ArgumentParser(description="Run Arcam AVR integration tests")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run only fast tests (exclude performance tests)"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run only performance tests"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel",
        "-j",
        type=int,
        default=1,
        help="Number of parallel test processes"
    )
    
    args = parser.parse_args()
    
    # Build pytest arguments
    pytest_args = [
        str(Path(__file__).parent),  # Test directory
        "--tb=short",  # Short traceback format
    ]
    
    if args.verbose:
        pytest_args.append("-v")
    
    if args.fast:
        pytest_args.extend(["-m", "not slow"])
        print("Running fast tests only...")
    elif args.performance:
        pytest_args.extend(["-m", "performance"])
        print("Running performance tests only...")
    else:
        print("Running all integration tests...")
    
    if args.coverage:
        pytest_args.extend([
            "--cov=homeassistant.components.arcam_avr",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=85"
        ])
        print("Coverage reporting enabled...")
    
    if args.parallel > 1:
        pytest_args.extend(["-n", str(args.parallel)])
        print(f"Running tests in {args.parallel} parallel processes...")
    
    # Run tests
    start_time = time.time()
    exit_code = pytest.main(pytest_args)
    end_time = time.time()
    
    # Print summary
    duration = end_time - start_time
    print(f"\nTest run completed in {duration:.2f} seconds")
    
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())