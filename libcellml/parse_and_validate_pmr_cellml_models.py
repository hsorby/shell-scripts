#!/usr/bin/env python

import argparse
import filecmp
import json
import os
import re
import subprocess
import sys

import requests

here = os.path.abspath(os.path.dirname(__file__))


def run_cellml_model(executable, model_file):
    return_code = subprocess.call(f"{executable} {model_file}", shell=True)
    return return_code


def _get_local_filename(model_url):
    filename = re.sub('https://models.physiomeproject.org/e/[^/]+/', '', model_url)
    filename = re.sub('https://models.physiomeproject.org/exposure/[^/]+/', '', filename)
    # with open('filenames.txt', 'a') as f:
    #     f.write(f"{filename}\n")

    return filename


def _get_duplicate_filename(filename):
    dup = 1
    dup_filename = f"{filename}_dup{dup}"
    while os.path.isfile(dup_filename):
        dup += 1
        dup_filename = f"{filename}_dup{dup}"

    return dup_filename


def _do_download_file(url, filename):
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunked:
                f.write(chunk)


def _download_file(url):
    local_filename = _get_local_filename(url)

    # NOTE the stream=True parameter below
    if os.path.isfile(local_filename):
        dup_local_filename = _get_duplicate_filename(local_filename)
        _do_download_file(url, dup_local_filename)
        if filecmp.cmp(local_filename, dup_local_filename, shallow=False):
            os.remove(dup_local_filename)
    else:
        _do_download_file(url, local_filename)

    return local_filename


def fetch_cellml_model(model_href_raw):
    model_href = re.sub('/view$', '', model_href_raw)
    return _download_file(model_href)


def _process_arguments():
    parser = argparse.ArgumentParser(description="Run through CellML models from PMR.")
    parser.add_argument("data",
                        help="JSON listing of CellML files available on PMR.")
    parser.add_argument("parse_validate_exe",
                        help="Parse and validate executable.")

    return parser.parse_args()


def main():
    args = _process_arguments()
    with open(args.data) as f:
        content = json.load(f)

    if "collection" in content and "links" in content["collection"]:

        current_dir = os.path.abspath(os.path.curdir)
        cellml_files_dir = os.path.join(current_dir, "cellml_files")
        if not os.path.isdir(cellml_files_dir):
            os.mkdir(cellml_files_dir)

        executable = args.parse_validate_exe
        if not os.path.isabs(executable):
            executable = os.path.join(current_dir, executable)

        os.chdir(cellml_files_dir)

        summary = {"model_count": 0}

        links = content["collection"]["links"]
        do_download = False
        if do_download:
            for index, link in enumerate(links):
                fetch_cellml_model(link["href"])

        def _add_result_to_summary(result_):
            summary["model_count"] += 1
            result_string = f"{result_}"
            if result_string not in summary:
                summary[result_string] = 1
            else:
                summary[result_string] += 1

        index = 0
        just_issues = False
        if just_issues:
            with open('../just_issues.txt') as f:
                lines = f.readlines()

            for line in lines:
                cellml_model_file = line.rstrip()
                result = run_cellml_model(executable, os.path.join(cellml_files_dir, cellml_model_file))
                _add_result_to_summary(result)
        else:
            for root, dirs, files in os.walk(".", topdown=False):
                for name in files:
                    cellml_model_file = os.path.join(root, name)
                    # result = 0
                    result = run_cellml_model(executable, os.path.join(cellml_files_dir, cellml_model_file))
                    _add_result_to_summary(result)
                    index += 1
                    # if index > 20:
                    #     break

        os.chdir(current_dir)
        with open("summary.json", "w") as f:
            json.dump(summary, f)

    else:
        return 1

    return 0


# {"model_count": 2551, "0": 1487, "2": 468, "1": 596}
# {"model_count": 2551, "0": 1614, "2": 514, "1": 423}
# {"model_count": 2183, "4": 2, "2": 480, "1": 313, "0": 1388}
if __name__ == "__main__":
    sys.exit(main())
