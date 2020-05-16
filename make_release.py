#!/usr/bin/env python3
import sys
import os
import json
from datetime import datetime
import pygit2 as git
import readline
from distutils import version
import subprocess as cmd

from analysis.gitdata import WholeHistory

HERE = os.path.dirname(os.path.abspath(__file__))
REPOSTAT_REPO_PATH = HERE
REPOSTAT_REPO = git.Repository(REPOSTAT_REPO_PATH)
REPOSTAT_MAILMAP = git.Mailmap.from_repository(REPOSTAT_REPO)
RELEASE_DATA_FILE = os.path.join(REPOSTAT_REPO_PATH, "tools", 'release_data.json')
CHANGELOG_FILE_NAME = "CHANGELOG.rst"


def rl_input(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def prepare_changelog(new_version):
    with open(CHANGELOG_FILE_NAME, 'r') as f:
        original_content = f.read()
    version_date = datetime.today().date()
    with open(CHANGELOG_FILE_NAME, 'w') as f:
        f.write(f"{new_version} ({version_date})\n")
        f.write("-------------------------\n\n")
        f.write(original_content)


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

print("Fetching contributors...")
wh = WholeHistory(REPOSTAT_REPO, REPOSTAT_REPO.head.shorthand).as_dataframe()
contributors = wh[['author_name', 'author_timestamp']].groupby(by='author_name').max()\
    .sort_values(by='author_timestamp', ascending=False).index.tolist()
release_data['contributors'] = contributors

with open(RELEASE_DATA_FILE, 'w') as release_json_file:
    print("Release data is being updated:", release_data)
    json.dump(release_data, release_json_file, indent=4)

# create commit with release data
user_name = REPOSTAT_REPO.config["user.name"]
user_email = REPOSTAT_REPO.config["user.email"]
author = git.Signature(user_name, user_email)

REPOSTAT_REPO.index.add(os.path.join("tools", 'release_data.json'))
REPOSTAT_REPO.index.add(CHANGELOG_FILE_NAME)
REPOSTAT_REPO.index.write()

print("\nNow release commit can be created and tagged via:\n")
print(f"git tag -s -a {new_version_tag} -m 'Release {new_version_tag}'")
