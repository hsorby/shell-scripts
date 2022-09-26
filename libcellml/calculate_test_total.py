#!/usr/bin/env python

import re
import sys


def main():
    captured_output = sys.argv[1]
    with open(captured_output) as f:
        lines = f.readlines()

    tot = 0
    for line in lines:
        a = re.search(r"^\d+: \[==========\] (\d+) tests from (\d+) test case[s]? ran.*", line)
        if a is not None:
            tot += int(a.group(1))

    print("Total test count: ", tot)


if __name__ == "__main__":
    main()

