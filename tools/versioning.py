from datetime import datetime

def generate_version_from(commit, hex_oid_symbols_count=7):
    commit_yymm = datetime.fromtimestamp(commit.author.time).strftime('%Y-%m')
    commit_hash = commit.hex[:hex_oid_symbols_count]
    return '{}.{}'.format(commit_yymm, commit_hash)



