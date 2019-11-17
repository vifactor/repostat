#!/usr/bin/env python3
import sys
import os
import json
from datetime import datetime
import pygit2 as git
import readline
from distutils import version

HERE = os.path.dirname(os.path.abspath(__file__))
REPOSTAT_REPO_PATH = HERE
REPOSTAT_REPO = git.Repository(REPOSTAT_REPO_PATH)
RELEASE_DATA_FILE = os.path.join(REPOSTAT_REPO_PATH, "tools", 'release_data.json')


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


# retrieve name of current branch
git_branch_string = REPOSTAT_REPO.head.shorthand
if git_branch_string != 'master':
    print("Not the 'master' branch: {}. Do not perform any actions.".format(git_branch_string))
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
    # TODO: give user a possibility to re-enter version
    print(f"New version {new_version_str} cannot be less or equal than the current one {current_version}.")
    sys.exit(0)

new_version_tag = f"v{new_version_str}"
repo_references_names = [ref.shorthand for ref in REPOSTAT_REPO.references.objects]
if new_version_tag in repo_references_names:
    print(f"Cannot create tag {new_version_tag}. Already exists.")
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
release_commit_oid = REPOSTAT_REPO.create_commit('refs/heads/master', author, committer,
                                                 release_commit_message, tree, [head_commit.hex])

# create (TODO: signed) annotated tag on release commit
tagger = author
release_tag_oid = REPOSTAT_REPO.create_tag(new_version_tag, release_commit_oid, git.GIT_OBJ_COMMIT, tagger,
                                           release_commit_message)
print("Commit ", release_commit_oid, " tagged with ", release_tag_oid)
