#!/usr/bin/env python3
"""
Test runner script for validating role YAML files.
This script runs all the tests and generates a report.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

def run_tests(verbose=False, report=False):
    """Run all the tests and generate a report."""
    print("Running tests to validate role YAML files...")
    
    # Build the pytest command
    cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if report:
        # Instead of measuring coverage for the role directory (which contains only YAML files),
        # measure coverage for the test files themselves
        cmd.extend(["--cov=tests", "--cov-report=term", "--cov-report=html"])
    
    # Add the test files
    cmd.append(str(PROJECT_ROOT / "tests"))
    
    # Run the tests
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print the output
    print(result.stdout)
    
    if result.stderr:
        print("Errors:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    
    # Return the exit code
    return result.returncode

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run tests to validate role YAML files.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-r", "--report", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    exit_code = run_tests(verbose=args.verbose, report=args.report)
    
    if exit_code == 0:
        print("All tests passed!")
    else:
        print(f"Tests failed with exit code {exit_code}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 