"""Test script utilities for grading projects, CS 210, Fall 2022"""
import sys
OK = True   # Flip to False if any test case fails

def init(catch_stdout: bool = True):
    if catch_stdout:
        sys.stdout = sys.stderr
    OK = True

def ok() -> bool:
    return OK

class Firewall:
    """Context manager facilitates running each test case with "expect"
    in a sandbox, catching and recovering from exceptions without aborting
    the whole program. 
    """
    def __init__(self, desc: str):
        self.desc = desc
        print(f"Testing {desc}", file=sys.stderr)

    def __enter__(self):
        print("(entered)")
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            print(f"Finished testing {self.desc}")
        else:
            OK = False
            print(f"Failed {self.desc} with exception", file=sys.stderr)
            print(f"Encountered exception of type {exc_type}: {exc_value}")

    def expect(self, desc, observed: object, expected: object):
        """Explanation of test success or failure"""
        global OK
        if expected == observed:
            print(f"+   Passed: {desc}", file=sys.stderr)
        else:
            OK = False
            print(f"*** Failed: {desc}", file=sys.stderr)
            print(f"  Expected: {expected}", file=sys.stderr)
            print(f"  Observed: {observed}", file=sys.stderr)

# Tests from doctests, and supplementary tests
