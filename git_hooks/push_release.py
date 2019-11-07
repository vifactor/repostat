#!/usr/bin/env python3
import sys
import subprocess
import re
import os
import json
from datetime import datetime
import pygit2 as git

HERE = os.path.dirname(os.path.abspath(__file__))
REPOSTAT_REPO_PATH = os.path.join(HERE, '..', '..')
REPOSTAT_REPO = git.Repository(REPOSTAT_REPO_PATH)
RELEASE_DATA_FILE = os.path.join(REPOSTAT_REPO_PATH, "tools", 'release_data.json')


def fetch_contributors(repo):
    head_commit = repo.head.peel()
    contribution = {}

    submodules_paths = repo.listall_submodules()
    for p in head_commit.tree.diff_to_tree():
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

# get most recent tag name in current branch
# TODO: go for earlier tags in history?
git_tag_string = REPOSTAT_REPO.describe(describe_strategy=git.GIT_DESCRIBE_TAGS, abbreviated_size=0)
# check if this is a version tag of type: vN.N[.N], e.g. "v0.1"
if re.fullmatch(r'^v\d+\.\d+(\.\d+)?\Z', git_tag_string):
    print('The most recent version tag is: ', git_tag_string)
else:
    print('The most recent is not a release version tag: ', git_tag_string)
    sys.exit(0)

try:
    release_json_file = open(RELEASE_DATA_FILE)
except FileNotFoundError as ex:
    release_data = {}
    print("{}: {}".format(ex.strerror, ex.filename))
else:
    release_data = json.load(release_json_file)
    print(release_data)
    release_json_file.close()

if not release_data or release_data['develop_version'] != git_tag_string:
    # create new release data and store, create commit
    release_data['develop_version'] = git_tag_string

    tag_object = REPOSTAT_REPO.revparse_single(git_tag_string)
    if isinstance(tag_object, git.Commit):
        release_commit = tag_object
    elif isinstance(tag_object, git.Tag):
        release_commit = tag_object.get_object()
    else:
        print("Unexpected tag object type {}".format(type(tag_object)))
        sys.exit(1)

    release_tag_timestamp = release_commit.author.time
    release_tag_date_yymmdd = datetime.fromtimestamp(release_tag_timestamp).strftime('%Y-%m-%d')
    release_data['user_version'] = release_tag_date_yymmdd

    # hash of release tag's commit (first 7 hex symbols like git describe)
    release_data['git_sha1'] = release_commit.hex[:7]

    contributors = fetch_contributors(REPOSTAT_REPO)
    release_data['contributors'] = contributors

    with open(RELEASE_DATA_FILE, 'w') as release_json_file:
        print("Release data is being updated:", release_data)
        json.dump(release_data, release_json_file, indent=4)

    # create commit with release data
    subprocess.check_output(['git', 'add', '{}'.format(RELEASE_DATA_FILE)])
    subprocess.check_output(['git', 'commit', '-m "Release {}"'.format(git_tag_string)])
    # move the most recent tag onto this new commit
    # TODO: move tag with message
    subprocess.check_output(['git', 'tag', '-f', git_tag_string])

# NOTE: for debug purposes (without push) use exit code different from 0
sys.exit(0)
