"""
This script creates a change log for the merged pull requests between two tags
in the cellml/libcellml repository.
If only one tag is given then the first commit is used for the starting point.

 - Requires 'git' to be present.
 - Requires Python requests library.

If only one tag is given then the other tag is considered to be HEAD.
If targeting

usage:
 python create_change_log.py v0.1.0 v0.2.0
"""
import json
import os
import requests
import subprocess
import sys

from pathlib import Path

DATABASE_FILE = 'pull_request.db'
FIRST_COMMIT_SHA = 'bdb8aea5cbfda734dc980470b98e861eba6a8a95'

pull_request_database = []
pull_request_cache = {}


class CommunicationError(Exception):
    pass


class MissingPullRequestData(Exception):
    pass


def _sort_pull_request_data(data):
    return sorted(data, key=lambda k: k['merged_at'] if k['merged_at'] is not None else '0000-00-00T00:00:00Z', reverse=True)


def _sort_summary_data(data):
    return sorted(data, key=lambda k: k['label'])


def _get_newest(pull_requests):
    if len(pull_requests) == 0:
        raise MissingPullRequestData('Pull request data is empty.')
    return pull_requests[0]


def _pull_request_merged_into_main(pull_request):
    was_merged = pull_request['merged_at'] is not None
    merged_into_main = pull_request['base']['ref'] == 'main' or pull_request['base']['ref'] == 'develop'
    return was_merged and merged_into_main


def _ask_github_for_pull_request_data(page=1):
    global pull_request_cache

    if page in pull_request_cache:
        return pull_request_cache[page]

    r = requests.get('https://api.github.com/repos/cellml/libcellml/pulls',
                     headers={'Accept': 'application/vnd.github.v3+json'},
                     params={'state': 'closed', 'page': page, 'per_page': 100})

    if r.status_code != 200:
        raise CommunicationError(f'Got status code {r.status_code} from Github.')

    content = r.content.decode('utf-8')
    page_pull_requests = _sort_pull_request_data(json.loads(content))
    merged_pull_requests = [x for x in page_pull_requests if _pull_request_merged_into_main(x)]

    pull_request_cache[page] = merged_pull_requests
    return merged_pull_requests


def load_database():
    global pull_request_database

    Path(DATABASE_FILE).touch()

    with open(DATABASE_FILE) as f:
        content = f.read()
        if content:
            pull_requests_loaded = json.loads(content)
            pull_request_database = _sort_pull_request_data(pull_requests_loaded)


def get_newest_database_entry():
    global pull_request_database

    return pull_request_database[0] if len(pull_request_database) else None


def database_up_to_date():
    # Get the most recent pull request.
    pull_requests = _ask_github_for_pull_request_data()
    newest_pull_request = _get_newest(pull_requests)
    # If the first one isn't in the database then the database isn't up to date.
    newest_database_entry = get_newest_database_entry()
    if newest_database_entry == newest_pull_request:
        return True

    return False


def add_entry_to_database(pull_request):
    global pull_request_database

    if pull_request not in pull_request_database:
        pull_request_database.append(pull_request)
        return True

    return False


def add_all_entries_to_database(pull_requests):
    global pull_request_database
    added_all = True

    for pull_request in pull_requests:
        added = add_entry_to_database(pull_request)
        if not added:
            added_all = False

    with open(DATABASE_FILE, 'w') as f:
        stringified_pull_requests = json.dumps(pull_request_database)
        f.write(stringified_pull_requests)

    return added_all


def update_database():
    # Keep asking for merged pull requests until there are none.
    page = 1
    pull_requests = _ask_github_for_pull_request_data(page)
    if not add_all_entries_to_database(pull_requests):
        return

    while len(pull_requests) > 0:
        page += 1
        pull_requests = _ask_github_for_pull_request_data(page)
        # Add any pull requests not in the database to it.
        if not add_all_entries_to_database(pull_requests):
            return


def clone_repository():
    subprocess.call(['git clone https://github.com/cellml/libcellml.git libcellml'], shell=True)


def _parse_tag_output(output):
    tag_data = {}
    lines = output.split('\n')
    for line in lines:
        parts = line.split(' ')
        if len(parts) > 1:
            tag_data[parts[0]] = ' '.join(parts[1:])

    return tag_data


def _get_tag_data(tag):
    cur_dir = os.path.abspath(os.curdir)

    pr = subprocess.Popen(f'git tag -v {tag}',
                          cwd=os.path.join(cur_dir, 'libcellml'),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          shell=True)
    (out, error) = pr.communicate()

    return _parse_tag_output(out.decode('utf-8'))


def _get_commit_time(commit_sha):
    cur_dir = os.path.abspath(os.curdir)

    pr = subprocess.Popen(f'TZ=UTC git show --date=iso-local --pretty=tformat:%cd {commit_sha}',
                          cwd=os.path.join(cur_dir, 'libcellml'),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          shell=True)
    (out, error) = pr.communicate()
    clean_time = out.decode('utf-8').splitlines()[0]
    split_time = clean_time.split(' ')

    return f'{split_time[0]}T{split_time[1]}Z'


def tag_is_valid(tag):
    if tag == '-' or tag == 'HEAD':
        return True

    tag_data = _get_tag_data(tag)
    return 'tag' in tag_data and tag_data['tag'] == tag


def tags_are_valid(tag_start, tag_end):
    if not tag_is_valid(tag_end):
        return False

    return tag_is_valid(tag_start)


def get_time_of_tag(tag):
    if tag == 'HEAD':
        commit_sha = 'HEAD'
    else:
        tag_data = _get_tag_data(tag)
        commit_sha = tag_data['object']

    return _get_commit_time(commit_sha)


def get_qualifying_pull_requests(start_time, end_time):
    global pull_request_database

    qualifying_pull_requests = []
    number_of_database_entries = len(pull_request_database)
    range_complete = False
    end_time_found = False
    start_time_found = False
    database_index = 0
    while not range_complete and database_index < number_of_database_entries:
        entry = pull_request_database[database_index]
        if not end_time_found:
            if entry['merged_at'] <= end_time:
                end_time_found = True
        elif not start_time_found:
            if entry['merged_at'] < start_time:
                start_time_found = True

        if end_time_found and not start_time_found:
            qualifying_pull_requests.append(entry)

        if start_time_found and end_time_found:
            range_complete = True

        database_index += 1

    return qualifying_pull_requests


def extract_label(pull_request):
    first_label = pull_request['labels'][0] if len(pull_request['labels']) else {}
    return first_label['name'] if 'name' in first_label else 'No category'


def extract_summary(pull_request):
    return {'title': pull_request['title'], 'label': extract_label(pull_request), 'number': pull_request['number'], 'url': pull_request['html_url']}


def write_out_to_changelog_file(sorted_summaries, tag_start, tag_end):
    current_label = ''
    file_name = f'changelog_{tag_start}_{tag_end}.rst'
    with open(file_name, 'w') as f:
        for summary in sorted_summaries:
            if current_label != summary['label']:
                current_label = summary['label']
                f.write(f'\n{current_label}\n')
                f.write('-' * len(current_label))
                f.write('\n\n')

            title = summary['title'][:-1] if summary['title'].endswith('.') else summary['title']
            f.write(f' * {title} [`#{summary["number"]} {summary["url"]}`_].\n')

    print(f'Changelog written to: {file_name}.')


def main():
    global pull_request_cache
    pull_request_cache = {}

    args = sys.argv[:]

    if len(args) > 1:
        tag_start = args.pop()
        tag_end = 'HEAD'
        if len(args) > 1:
            tag_end = tag_start
            tag_start = args.pop()
        if tag_start == '-':
            tag_start = FIRST_COMMIT_SHA
    else:
        sys.exit(1)

    load_database()
    # Determine if the database is complete.
    if not database_up_to_date():
        # Update database if not complete.
        update_database()

    if not os.path.isfile(os.path.join('libcellml', 'CMakeLists.txt')):
        clone_repository()

    # Check tags, abort on error.
    if not tags_are_valid(tag_start, tag_end):
        return sys.exit(2)

    # Get time from tagged commit.
    start_time = get_time_of_tag(tag_start)
    end_time = get_time_of_tag(tag_end)

    # Go through database looking for merged pull requests between end time and start time (inclusive).
    pull_requests = get_qualifying_pull_requests(start_time, end_time)
    # For each pull request extract the title and label (if present).
    pull_request_change_summaries = []
    for pull_request in pull_requests:
        pull_request_change_summaries.append(extract_summary(pull_request))

    # Sort the summaries.
    sorted_summaries = _sort_summary_data(pull_request_change_summaries)

    # Create a reStructureText file to dump change log into.
    write_out_to_changelog_file(sorted_summaries, tag_start, tag_end)


if __name__ == "__main__":
    main()
