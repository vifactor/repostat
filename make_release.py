#!/usr/bin/env python3
import sys
import os
import re
import json
from datetime import datetime
import pygit2 as git
import readline
from distutils import version
import subprocess as cmd

HERE = os.path.dirname(os.path.abspath(__file__))
REPOSTAT_REPO_PATH = HERE
REPOSTAT_REPO = git.Repository(REPOSTAT_REPO_PATH)
RELEASE_DATA_FILE = os.path.join(REPOSTAT_REPO_PATH, "tools", 'release_data.json')
CHANGELOG_FILE_NAME = "CHANGELOG.rst"


def rl_input(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def fetch_contributors(repo):
    contribution = {}

    submodules_paths = repo.listall_submodules()
    for p in repo.head.peel().tree.diff_to_tree():
        file_to_blame = p.delta.new_file.path
        if file_to_blame not in submodules_paths:
            blob_blame = repo.blame(file_to_blame)
            for blame_hunk in blob_blame:
                contribution[blame_hunk.final_committer.name] = contribution.get(blame_hunk.final_committer.name, 0) \
                                                                + blame_hunk.lines_in_hunk

    # this gives only the contributors to the current code tree, not all the commiters to the project
    contribution = sorted(contribution.items(), key=lambda kv: kv[1], reverse=True)
    return [contributor for contributor, lines_contributed in contribution]


def prepare_changelog(new_version):
    with open(CHANGELOG_FILE_NAME, 'r') as f:
        original_content = f.read()
    version_date = datetime.today().date()
    with open(CHANGELOG_FILE_NAME, 'w') as f:
        f.write(f"{new_version} ({version_date})\n")
        f.write("-------------------------\n\n")
        f.write(original_content)


# retrieve name of current branch
git_branch_string = REPOSTAT_REPO.head.shorthand

is_master_branch = (git_branch_string == 'master')
is_release_branch = re.search(r'v(\d+.\d+).x', git_branch_string) is not None
if not (is_master_branch or is_release_branch):
    print("Not the 'master' or a release branch: {}. Do not perform any actions.".format(git_branch_string))
    sys.exit(0)

current_version_str = '0.0.0'
try:
    release_json_file = open(RELEASE_DATA_FILE)
except FileNotFoundError as ex:
    release_data = {}
    print("{}: {}".format(ex.strerror, ex.filename))
else:
    release_data = json.load(release_json_file)
    release_json_file.close()
    current_version_str = release_data.get('develop_version', current_version_str)
    print(f"Current version is: {current_version_str}")

# remove "v"-prefix of the version string
current_version = version.StrictVersion(current_version_str[1:])
current_version_tuple = version.StrictVersion(current_version_str[1:]).version
new_version_str = f'{current_version_tuple[0]}.{current_version_tuple[1] + 1}.{current_version_tuple[2]}'

# editable command-line prompt to enter new version
new_version_str = rl_input("Enter new version: v", prefill=new_version_str)

if version.StrictVersion(new_version_str) <= current_version:
    print(f"New version {new_version_str} cannot be less or equal than the current one {current_version}.")
    sys.exit(0)

new_version_tag = f"v{new_version_str}"
repo_references_names = [ref.shorthand for ref in REPOSTAT_REPO.references.objects]
if new_version_tag in repo_references_names:
    print(f"Cannot create tag {new_version_tag}. Already exists.")
    sys.exit(0)

# changelog file prepended with new section for the new version
prepare_changelog(new_version_str)
EDITOR = "nano"
# start editor to add changelog entries
retcode = cmd.call([EDITOR, CHANGELOG_FILE_NAME])
if retcode != 0:
    print("Could not start editor to modify changelog")
    sys.exit(0)

# create new release data and store, create commit
release_data['develop_version'] = new_version_tag

# release_data.json is going to contain data (timestamp, hash, etc.) from current head commit
# because "release" commit does not exist at this point
head_commit = REPOSTAT_REPO.head.peel()
release_tag_date_yymmdd = datetime.fromtimestamp(head_commit.author.time).strftime('%Y-%m-%d')
release_data['user_version'] = release_tag_date_yymmdd
# hash of release tag's commit (first 7 hex symbols like git describe)
release_data['git_sha1'] = head_commit.hex[:7]
print("Fetching contributors...")
contributors = fetch_contributors(REPOSTAT_REPO)
release_data['contributors'] = contributors

with open(RELEASE_DATA_FILE, 'w') as release_json_file:
    print("Release data is being updated:", release_data)
    json.dump(release_data, release_json_file, indent=4)

# create commit with release data
user_name = REPOSTAT_REPO.config["user.name"]
user_email = REPOSTAT_REPO.config["user.email"]
author = git.Signature(user_name, user_email)
committer = author

REPOSTAT_REPO.index.add_all()
REPOSTAT_REPO.index.write()
tree = REPOSTAT_REPO.index.write_tree()

release_commit_message = f"Release {new_version_tag}"
print("Now release commit can be created and tagged via:")
print(f"git tag -s -a {new_version_tag} -m '{release_commit_message}'")
