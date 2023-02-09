# This script checks for changes to a repository from the last tag.
# It is focused on looking at the repositories used by the mapclientreleasescripts repository.
# To determine if updates are required to the list of plugins or workflows to include in a release.
import argparse
import os
import requests
import sys

from datetime import datetime
from packaging.version import Version


HEADERS = {'Authorization': 'token ' + os.environ.get("GITHUB_PAT", "")}
GITHUB_API_URL_TAGS_TEMPLATE = "https://api.github.com/repos/{owner}/{repo}/tags"
GITHUB_API_URL_LAST_COMMIT_TEMPLATE = "https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"


def _determine_organisation_and_repo_name(repo):
    *_, a, b = repo.split("/")

    return a, b.replace(".git", "")


def _review_tags(organisation, repo):
    url = GITHUB_API_URL_TAGS_TEMPLATE.format(owner=organisation, repo=repo)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()[0]
    else:
        print(f"URL: {url} returned status code: {response.status_code}!")

    return None


def _last_commit_sha(organisation, repo):
    url = GITHUB_API_URL_LAST_COMMIT_TEMPLATE.format(owner=organisation, repo=repo)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        json_response = response.json()
        return json_response[0]['sha']
    else:
        print(f"URL: {url} returned status code: {response.status_code}!")

    return None


def _process_repository_list(content):
    for line in content:
        line = line.rstrip()
        parts = line.split(" ")
        if len(parts) == 1:
            repo = parts[0]
            tag = None
        elif len(parts) == 2:
            repo = parts[0]
            tag = parts[1]
        else:
            sys.exit(2)

        organisation, repo_name = _determine_organisation_and_repo_name(repo)
        report = _review_tags(organisation, repo_name)
        if report is not None:
            if tag is not None and Version(tag) < Version(report["name"]):
                print(f"New version available! {repo} {tag} {report['name']}")
            else:
                result = _last_commit_sha(organisation, repo_name)
                if result != report["commit"]["sha"]:
                    print(f"New changes available! {repo}")


def _process_repository_listing(_file):
    with open(_file) as f:
        content = f.readlines()

    return content


def _process_file_listing_file(_file):
    with open(_file) as f:
        content = f.readlines()

    combined_content = []
    for line in content:
        file_name = line.rstrip()
        combined_content.extend(_process_repository_listing(file_name))

    return combined_content


def _do_rate_report():
    response = requests.get("https://api.github.com/rate_limit", headers=HEADERS)
    json_response = response.json()
    human_time = datetime.fromtimestamp(json_response["resources"]["core"]["reset"]).strftime('%c')
    limit = json_response["resources"]["core"]["limit"]
    used = json_response["resources"]["core"]["used"]
    remaining = json_response["resources"]["core"]["remaining"]
    report = f"Rate limits report:\n  limit: {limit}\n  used: {used}\n  remaining: {remaining}\n  reset: {human_time}"
    print(report)


def _parse_args():
    parser = argparse.ArgumentParser(prog="check_for_post_release_updates")
    parser.add_argument("repository_listing", nargs="?", help="A file containing a list of repositories to check.")
    parser.add_argument("-f", "--file", help="A file containing a list of files that themselves list repositories to check.")
    parser.add_argument("-r", "--rate-limit", action="store_true", help="Report on GitHub API rate limit.")
    return parser.parse_args()


def main():
    args = _parse_args()

    args_ok = False
    repository_listing_file = None
    file_listing_file = None
    if args.repository_listing is not None:
        args_ok = os.path.isfile(args.repository_listing)
        repository_listing_file = args.repository_listing

    if args.file is not None:
        args_ok = os.path.isfile(args.file)
        file_listing_file = args.file

    if not args_ok:
        sys.exit(1)

    if args.rate_limit:
        _do_rate_report()
        sys.exit(0)

    if file_listing_file:
        content = _process_file_listing_file(file_listing_file)
    else:
        content = _process_repository_listing(repository_listing_file)

    _process_repository_list(content)


if __name__ == "__main__":
    main()

# [{'sha': '4b0d5de65472d0831c5e983108fa6757518488cd', 'node_id': 'C_kwDOFhW4o9oAKDRiMGQ1ZGU2NTQ3MmQwODMxYzVlOTgzMTA4ZmE2NzU3NTE4NDg4Y2Q', 'commit': {'author': {'name': 'Hugh Sorby', 'email': 'h.sorby@auckland.ac.nz', 'date': '2022-08-04T01:27:17Z'}, 'committer': {'name': 'GitHub', 'email': 'noreply@github.com', 'date': '2022-08-04T01:27:17Z'}, 'message': 'Merge pull request #3 from Kayvv/main\n\nAdd documentation link on configure dialog', 'tree': {'sha': 'e72592eded951afb6e39ca0e7b975511195f9b06', 'url': 'https://api.github.com/repos/ABI-Software/mapclientplugins.mbfxml2exconverterstep/git/trees/e72592eded951afb6e39ca0e7b975511195f9b06'}, 'url': 'https://api.github.com/repos/ABI-Software/mapclientplugins.mbfxml2exconverterstep/git/commits/4b0d5de65472d0831c5e983108fa6757518488cd', 'comment_count': 0, 'verification': {'verified': True, 'reason': 'valid', 'signature': '-----BEGIN PGP SIGNATURE-----\n\nwsBcBAABCAAQBQJi6yB1CRBK7hj4Ov3rIwAASY4IABTYotdwdPgz0bmPqwD+GX9C\nURObROBl9FF3lHwafrghmYJ1c7iEntL6ubLxcrQ/R7SlG++CH/CAFBTUmC0VSmgl\nCcjwEOqWDG7VP6fQswPludlnKH9dHC84BArNc6+oqiN73FsRXnh5lf8myOcMmuoi\nhmJ7bp0s3pQsAlU6uxgEICJtoFohTY02eTOnM0j2SS2iCY5ivjUBBtG37B8LzLVO\nlHlbEJjmPQT+2i6uIF/IQPTcU1W2q9yqobfkF54NPmXxmuKMkyzDM5ko//LqcIT7\nw0OLhcazmir9sUCaahH+3T6ZDtuOJy2yVNcy+tpLBPz+qoYlxyJu7KTGHp68YOs=\n=4Kii\n-----END PGP SIGNATURE-----\n', 'payload': 'tree e72592eded951afb6e39ca0e7b975511195f9b06\nparent d1bfe943391b3f00d7b6381e9d98594dcb1285bd\nparent 2c399152d2e47b66a187e3bd537c3c9dd224e9f6\nauthor Hugh Sorby <h.sorby@auckland.ac.nz> 1659576437 +1200\ncommitter GitHub <noreply@github.com> 1659576437 +1200\n\nMerge pull request #3 from Kayvv/main\n\nAdd documentation link on configure dialog'}}, 'url': 'https://api.github.com/repos/ABI-Software/mapclientplugins.mbfxml2exconverterstep/commits/4b0d5de65472d0831c5e983108fa6757518488cd', 'html_url': 'https://github.com/ABI-Software/mapclientplugins.mbfxml2exconverterstep/commit/4b0d5de65472d0831c5e983108fa6757518488cd', 'comments_url': 'https://api.github.com/repos/ABI-Software/mapclientplugins.mbfxml2exconverterstep/commits/4b0d5de65472d0831c5e983108fa6757518488cd/comments', 'author': {'login': 'hsorby', 'id': 778048, 'node_id': 'MDQ6VXNlcjc3ODA0OA==', 'avatar_url': 'https://avatars.githubusercontent.com/u/778048?v=4', 'gravatar_id': '', 'url': 'https://api.github.com/users/hsorby', 'html_url': 'https://github.com/hsorby', 'followers_url': 'https://api.github.com/users/hsorby/followers', 'following_url': 'https://api.github.com/users/hsorby/following{/other_user}', 'gists_url': 'https://api.github.com/users/hsorby/gists{/gist_id}', 'starred_url': 'https://api.github.com/users/hsorby/starred{/owner}{/repo}', 'subscriptions_url': 'https://api.github.com/users/hsorby/subscriptions', 'organizations_url': 'https://api.github.com/users/hsorby/orgs', 'repos_url': 'https://api.github.com/users/hsorby/repos', 'events_url': 'https://api.github.com/users/hsorby/events{/privacy}', 'received_events_url': 'https://api.github.com/users/hsorby/received_events', 'type': 'User', 'site_admin': False}, 'committer': {'login': 'web-flow', 'id': 19864447, 'node_id': 'MDQ6VXNlcjE5ODY0NDQ3', 'avatar_url': 'https://avatars.githubusercontent.com/u/19864447?v=4', 'gravatar_id': '', 'url': 'https://api.github.com/users/web-flow', 'html_url': 'https://github.com/web-flow', 'followers_url': 'https://api.github.com/users/web-flow/followers', 'following_url': 'https://api.github.com/users/web-flow/following{/other_user}', 'gists_url': 'https://api.github.com/users/web-flow/gists{/gist_id}', 'starred_url': 'https://api.github.com/users/web-flow/starred{/owner}{/repo}', 'subscriptions_url': 'https://api.github.com/users/web-flow/subscriptions', 'organizations_url': 'https://api.github.com/users/web-flow/orgs', 'repos_url': 'https://api.github.com/users/web-flow/repos', 'events_url': 'https://api.github.com/users/web-flow/events{/privacy}', 'received_events_url': 'https://api.github.com/users/web-flow/received_events', 'type': 'User', 'site_admin': False}, 'parents': [{'sha': 'd1bfe943391b3f00d7b6381e9d98594dcb1285bd', 'url': 'https://api.github.com/repos/ABI-Software/mapclientplugins.mbfxml2exconverterstep/commits/d1bfe943391b3f00d7b6381e9d98594dcb1285bd', 'html_url': 'https://github.com/ABI-Software/mapclientplugins.mbfxml2exconverterstep/commit/d1bfe943391b3f00d7b6381e9d98594dcb1285bd'}, {'sha': '2c399152d2e47b66a187e3bd537c3c9dd224e9f6', 'url': 'https://api.github.com/repos/ABI-Software/mapclientplugins.mbfxml2exconverterstep/commits/2c399152d2e47b66a187e3bd537c3c9dd224e9f6', 'html_url': 'https://github.com/ABI-Software/mapclientplugins.mbfxml2exconverterstep/commit/2c399152d2e47b66a187e3bd537c3c9dd224e9f6'}]}]
