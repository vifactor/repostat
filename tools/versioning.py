from datetime import datetime

def generate_version_from(commit, hex_oid_symbols_count=7):
    commit_yymm = datetime.fromtimestamp(commit.author.time).strftime('%Y-%m')
    commit_hash = commit.hex[:hex_oid_symbols_count]
    return '{}.{}'.format(commit_yymm, commit_hash)


def fetch_contributors_from(repo, commit):
    contribution = {}
    submodules_paths = repo.listall_submodules()
    for p in commit.tree.diff_to_tree():
        file_to_blame = p.delta.new_file.path
        if file_to_blame not in submodules_paths:
            blob_blame = repo.blame(file_to_blame)
            for blame_hunk in blob_blame:
                contribution[blame_hunk.final_committer.name] = contribution.get(blame_hunk.final_committer.name, 0) \
                                                                + blame_hunk.lines_in_hunk

    # this gives only the contributors to the current code tree, not all the commiters to the project
    contribution = sorted(contribution.items(), key=lambda kv: kv[1], reverse=True)

    return [contributor for contributor, lines_contributed in contribution]
