#!/usr/bin/env python3

import re
import sys

if len(sys.argv) < 2:
    sys.exit(1)

cfgcmd_file = sys.argv[1]

with open(cfgcmd_file) as f:
    contents = f.read()


def contains_spaces(str):
    match = re.search('\s', str)
    return match is not None


def contains_semi_colon(str):
    match = re.search(';', str)
    return match is not None


match = re.search("cmd='(.*)'", contents)
if match:
    cmd = match.group(1)
    cmd = cmd.replace(';<SOURCE_DIR><SOURCE_SUBDIR>', '')
    split_cmd = cmd.split(';')
    extracted_cmd = ''
    for part in split_cmd:
        part = part.replace('<semi-colon>', ';')
        quote = True if contains_semi_colon(part) else True if contains_spaces(part) else False
        if quote:
            spaced_part = re.search('-([DG])(.*)', part)
            print(part, spaced_part)
            part = f'-{spaced_part.group(1)}"{spaced_part.group(2)}"'
        extracted_cmd += ' ' + part

    print(extracted_cmd)

else:
    sys.exit(2)

