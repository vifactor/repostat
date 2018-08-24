from __future__ import unicode_literals
import pygit2 as git
from datetime import datetime, tzinfo, timedelta


class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset):
        self.__offset = timedelta(minutes=offset)

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        # we don't know the time zone's name
        return None

    def dst(self, dt):
        # we don't know about DST
        return timedelta(0)


def split_email_address(email_address):
    parts = email_address.split('@')
    if len(parts) != 2:
        raise ValueError('Not an email passed: %s' % email_address)
    return parts[0], parts[1]


class GitStatistics:
    def __init__(self, path):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        self.authors = self.fetch_authors_info()
        self.tags = self.fetch_tags_info()
        self.domains = self.fetch_domains_info()
        self.timezones = self.fetch_timezone_info()
        self.first_commit_timestamp = min(commit.author.time for commit in self.repo.walk(self.repo.head.target))
        self.last_commit_timestamp = max(commit.author.time for commit in self.repo.walk(self.repo.head.target))
        self.active_days = {datetime.fromtimestamp(commit.author.time).strftime('%Y-%m-%d')
                            for commit in self.repo.walk(self.repo.head.target)}

    def fetch_authors_info(self):
        """
        e.g.
        {'Stefano Mosconi': {'lines_removed': 1, 'last_commit_stamp': 1302027851, 'active_days': set(['2011-04-05']),
                             'lines_added': 1, 'commits': 1, 'first_commit_stamp': 1302027851,
                             'last_active_day': '2011-04-05'}
        """
        result = {}
        for child_commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TIME):
            is_merge_commit = False
            if len(child_commit.parents) == 0:
                # initial commit
                st = child_commit.tree.diff_to_tree(swap=True).stats
            elif len(child_commit.parents) == 1:
                parent_commit = child_commit.parents[0]
                st = self.repo.diff(parent_commit, child_commit).stats
            else:  # if len(child_commit.parents) == 2 (merge commit)
                is_merge_commit = True
            commit_day_str = datetime.fromtimestamp(child_commit.author.time).strftime('%Y-%m-%d')
            author_name = child_commit.author.name.encode('utf-8')
            if author_name not in result:
                result[author_name] = {
                    'lines_removed': st.deletions if not is_merge_commit else 0,
                    'lines_added': st.insertions if not is_merge_commit else 0,
                    'active_days': {commit_day_str},
                    'commits': 1,
                    'first_commit_stamp': child_commit.author.time,
                    'last_commit_stamp': child_commit.author.time,
                }
            else:
                result[author_name]['lines_removed'] += st.deletions if not is_merge_commit else 0
                result[author_name]['lines_added'] += st.insertions if not is_merge_commit else 0
                result[author_name]['active_days'].add(commit_day_str)
                result[author_name]['commits'] += 1
                if result[author_name]['first_commit_stamp'] > child_commit.author.time:
                    result[author_name]['first_commit_stamp'] = child_commit.author.time
                if result[author_name]['last_commit_stamp'] < child_commit.author.time:
                    result[author_name]['last_commit_stamp'] = child_commit.author.time

        # it seems that there is a mistake (or my misunderstanding) in 'last_active_day' value
        # my calculations give are not the same as those done by Heikki Hokkanen for this parameter
        for author in result:
            last_active_day = datetime.fromtimestamp(result[author]['last_commit_stamp']).strftime('%Y-%m-%d')
            result[author]['last_active_day'] = last_active_day

        return result

    def fetch_tags_info(self):
        tags = filter(lambda refobj: refobj.name.startswith('refs/tags'), self.repo.listall_reference_objects())
        commit_tag = {refobj.peel().oid: refobj.shorthand for refobj in tags}

        result = {refobj.shorthand: {
            'stamp': refobj.peel().author.time,
            'date': datetime.fromtimestamp(refobj.peel().author.time).strftime('%Y-%m-%d'),
            'hash': str(refobj.target)} for refobj in tags}

        authors = {}
        commit_count = 0
        for commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL | git.GIT_SORT_REVERSE):
            commit_count += 1
            authors[commit.author.name] = authors.get(commit.author.name, 0) + 1
            if commit.oid in commit_tag.keys():
                tagname = commit_tag[commit.oid]
                result[tagname]['commits'] = commit_count
                result[tagname]['authors'] = authors

                commit_count = 0
                authors = {}

        return result

    def fetch_domains_info(self):
        result = {}
        for commit in self.repo.walk(self.repo.head.target):
            _, domain = split_email_address(commit.author.email)
            result[domain] = result.get(domain, 0) + 1
        # TODO: this is done to save compatibility with gitstats' structures
        result = {k: {'commits': v} for k, v in result.items()}
        return result

    def fetch_timezone_info(self):
        result = {}
        for commit in self.repo.walk(self.repo.head.target):
            # hint from https://github.com/libgit2/pygit2/blob/master/docs/recipes/git-show.rst
            tz = FixedOffset(commit.author.offset)
            dt = datetime.fromtimestamp(float(commit.author.time), tz)
            timezone_str = dt.strftime('%z')
            result[timezone_str] = result.get(timezone_str, 0) + 1
        return result
