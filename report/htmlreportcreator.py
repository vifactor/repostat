import os
import datetime
import calendar
import collections
import json
from jinja2 import Environment, FileSystemLoader
import pandas as pd

from analysis.gitstatistics import GitStatistics
from analysis.gitrepository import GitRepository
from tools.configuration import Configuration
from tools import sort_keys_by_value_of_key

from . import colormaps
from .html_page import HtmlPage, JsPlot

HERE = os.path.dirname(os.path.abspath(__file__))


class HTMLReportCreator:
    recent_activity_period_weeks = 32
    assets_subdir = "assets"
    templates_subdir = "templates"

    def __init__(self, config: Configuration, repo_stat: GitStatistics, repository: GitRepository):
        self.path = None
        self.configuration = config
        self.assets_path = os.path.join(HERE, self.assets_subdir)
        self.git_repo_statistics = repo_stat
        self.git_repository_statistics = repository
        self.has_tags_page = config.do_process_tags()
        self._time_sampling_interval = "W"
        self._do_generate_index_page = False

        templates_dir = os.path.join(HERE, self.templates_subdir)
        self.j2_env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True)
        self.j2_env.filters['to_month_name_abr'] = lambda im: calendar.month_abbr[im]
        self.j2_env.filters['to_weekday_name'] = lambda i: calendar.day_name[i]
        self.j2_env.filters['to_ratio'] = lambda val, max_val: (float(val) / max_val) if max_val != 0 else 0
        self.j2_env.filters['to_percentage'] = lambda val, max_val: (100 * float(val) / max_val) if max_val != 0 else 0
        colors = colormaps.colormaps[self.configuration['colormap']]
        self.j2_env.filters['to_heatmap'] = lambda val, max_val: "%d, %d, %d" % colors[int(float(val) / max_val * (len(colors) - 1))]

    def set_time_sampling(self, offset: str):
        """
        :param offset: any valid string composed of Pandas' offset aliases
            https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
        """
        self._time_sampling_interval = offset
        return self

    def generate_index_page(self, do_generate: bool = True):
        self._do_generate_index_page = do_generate
        return self

    def _get_recent_activity_data(self):
        recent_weekly_commits = self.git_repository_statistics.\
            get_recent_weekly_activity(self.recent_activity_period_weeks)

        values = [
            {
                'x': int(self.recent_activity_period_weeks - i - 1),
                'y': int(commits)
            } for i, commits in enumerate(recent_weekly_commits)
        ]
        graph_data = {
            "config": {
                "noData": "No recent activity.",
                "padData": True,
                "showXAxis": True,
                "xDomain": [self.recent_activity_period_weeks - 1, 0]
            },
            "data": [
                {'key': "Commits", 'color': "#9400D3", 'values': values}
            ]
        }

        return graph_data

    def _bundle_assets(self):
        from distutils.dir_util import copy_tree
        # copy assets to report output folder
        assets_local_abs_path = os.path.join(self.path, self.assets_subdir)
        copy_tree(src=self.assets_path, dst=assets_local_abs_path)
        # relative path to assets to embed into html pages
        self.assets_path = os.path.relpath(assets_local_abs_path, self.path)

    def _squash_authors_history(self, authors_history, max_authors_count):
        authors = self.git_repository_statistics.authors.sort(by='commits_count').names()

        most_productive_authors = authors[:max_authors_count]
        rest_authors = authors[max_authors_count:]

        most_productive_authors_history = authors_history[most_productive_authors] \
            .asfreq(freq=self._time_sampling_interval, fill_value=0) \
            .cumsum()
        rest_authors_history = authors_history[rest_authors].sum(axis=1)\
            .asfreq(freq=self._time_sampling_interval, fill_value=0)\
            .cumsum()

        most_productive_authors_history['Others'] = rest_authors_history.values
        return most_productive_authors_history

    def create(self, path):
        self.path = path

        if self.configuration.is_report_relocatable():
            self._bundle_assets()
        HtmlPage.set_assets_path(self.assets_path)

        pages = [
            self.make_general_page(),
            self.make_activity_page(),
            self.make_authors_page(),
            self.make_files_page(),
        ]
        if self.has_tags_page:
            pages.append(self.make_tags_page())
        pages.append(self.make_about_page())

        # render and save all pages
        for page in pages:
            rendered_page = page.render(self.j2_env, pages)
            page.save(self.path, rendered_page)

        if self._do_generate_index_page:
            # make the landing page for a web server
            from shutil import copyfile
            copyfile(os.path.join(path, "general.html"), os.path.join(path, "index.html"))

    def make_general_page(self):
        date_format_str = '%Y-%m-%d %H:%M'
        first_commit_datetime = datetime.datetime.fromtimestamp(self.git_repository_statistics.first_commit_timestamp)
        last_commit_datetime = datetime.datetime.fromtimestamp(self.git_repository_statistics.last_commit_timestamp)

        project_data = {
            "name": self.git_repo_statistics.repo_name,
            "branch": self.git_repo_statistics.analysed_branch,
            "age": (last_commit_datetime - first_commit_datetime).days,
            "active_days_count": self.git_repository_statistics.active_days_count,
            "commits_count": self.git_repository_statistics.total_commits_count,
            "merge_commits_count": self.git_repository_statistics.merge_commits_count,
            "authors_count": self.git_repository_statistics.authors.count(),
            "files_count": self.git_repo_statistics.total_files_count,
            "total_lines_count": self.git_repository_statistics.total_lines_count,
            "added_lines_count": self.git_repository_statistics.total_lines_added,
            "removed_lines_count": self.git_repository_statistics.total_lines_removed,
            "first_commit_date": first_commit_datetime.strftime(date_format_str),
            "last_commit_date": last_commit_datetime.strftime(date_format_str),
        }

        generation_data = {
            "datetime": datetime.datetime.today().strftime(date_format_str)
        }

        page = HtmlPage(name="General",
                        project=project_data,
                        generation=generation_data)
        return page

    def make_activity_page(self):
        # TODO: this conversion from old 'data' to new 'project data' should perhaps be removed in future
        project_data = {
            'timezones_activity': collections.OrderedDict(
                sorted(self.git_repository_statistics.timezones_distribution.items(), key=lambda n: int(n[0]))),
            'month_in_year_activity': self.git_repository_statistics.month_of_year_distribution.to_dict()
        }

        wd_h_distribution = self.git_repository_statistics.weekday_hour_distribution.astype('int32')
        project_data['weekday_hourly_activity'] = wd_h_distribution
        project_data['weekday_hour_max_commits_count'] = wd_h_distribution.max().max()
        project_data['weekday_activity'] = wd_h_distribution.sum(axis=1)
        project_data['hourly_activity'] = wd_h_distribution.sum(axis=0)

        page = HtmlPage(name='Activity', project=project_data)
        page.add_plot(self.make_activity_plot())

        return page

    def make_activity_plot(self) -> JsPlot:
        recent_activity = self._get_recent_activity_data()

        # Commits by current year's months
        current_year = datetime.date.today().year
        current_year_monthly_activity = self.git_repository_statistics.history('m')
        current_year_monthly_activity = current_year_monthly_activity \
            .loc[current_year_monthly_activity.index.year == current_year]

        current_year_monthly_activity = pd.Series(current_year_monthly_activity.values,
                                                  index=current_year_monthly_activity.index.month).to_dict()
        values = [
            {
                'x': imonth,
                'y': current_year_monthly_activity.get((imonth + 1), 0)
            } for imonth in range(0, 12)
        ]
        by_month = {
            "yAxis": {"axisLabel": "Commits in %d" % current_year},
            "xAxis": {"rotateLabels": -90, "ticks": len(values)},
            "data": [
                {"key": "Commits", "color": "#9400D3", "values": values}
            ]
        }

        # Commits by year
        yearly_activity = self.git_repository_statistics.history('Y')
        values = [{'x': int(x.year), 'y': int(y)} for x, y in zip(yearly_activity.index, yearly_activity.values)]

        by_year = {
            "xAxis": {"rotateLabels": -90, "ticks": len(values)},
            "yAxis": {"axisLabel": "Commits"},
            "data": [
                {"key": "Commits", "color": "#9400D3", "values": values}
            ]
        }

        review_duration = [
            {
                "label": label,
                "value": count
            }
            for label, count in self.git_repository_statistics.review_duration_distribution.items()
        ]

        activity_plot = JsPlot('activity.js',
                               commits_by_month=json.dumps(by_month),
                               commits_by_year=json.dumps(by_year),
                               recent_activity=json.dumps(recent_activity),
                               review_duration=json.dumps(review_duration),
                               )
        return activity_plot

    def make_authors_page(self):
        authors_summary = self.git_repository_statistics.authors.summary \
            .sort_values(by="commits_count", ascending=False)

        top_authors_statistics = authors_summary[:self.configuration['max_authors']]
        non_top_authors_names = authors_summary[self.configuration['max_authors']:]['author_name'].values
        project_data = {
            'top_authors_statistics': top_authors_statistics,
            'non_top_authors': non_top_authors_names,
            'authors_top': self.configuration['authors_top'],
            'total_commits_count': self.git_repository_statistics.total_commits_count,
            'total_lines_count': self.git_repository_statistics.total_lines_count,
            'do_plot_contribution': True if self.git_repo_statistics.contribution else False
        }

        raw_authors_data = self.git_repository_statistics.get_authors_ranking_by_month()
        ordered_months = raw_authors_data.index.get_level_values(0).unique().sort_values(ascending=False)
        project_data['months'] = []
        for yymm in ordered_months[0:self.configuration['max_authors_of_months']]:
            authors_in_month = raw_authors_data.loc[yymm]
            project_data['months'].append({
                'date': yymm,
                'top_author': {'name': authors_in_month.index[0], 'commits_count': authors_in_month[0]},
                'next_top_authors': ', '.join(list(authors_in_month.index[1:5])),
                'all_commits_count': authors_in_month.sum(),
                'total_authors_count': authors_in_month.size
            })

        project_data['years'] = []
        raw_authors_data = self.git_repository_statistics.get_authors_ranking_by_year()
        max_top_authors_index = self.configuration['authors_top'] + 1
        ordered_years = raw_authors_data.index.get_level_values(0).unique().sort_values(ascending=False)
        for y in ordered_years:
            authors_in_year = raw_authors_data.loc[y]
            project_data['years'].append({
                'date': y,
                'top_author': {'name': authors_in_year.index[0], 'commits_count': authors_in_year[0]},
                'next_top_authors': ', '.join(list(authors_in_year.index[1:max_top_authors_index])),
                'all_commits_count': authors_in_year.sum(),
                'total_authors_count': authors_in_year.size
            })

        page = HtmlPage('Authors', project=project_data)
        page.add_plot(self.make_authors_plot())
        return page

    def make_authors_plot(self) -> JsPlot:
        max_authors_per_plot_count = self.configuration['max_plot_authors_count']

        authors_activity_history = self.git_repository_statistics.authors.history(self._time_sampling_interval)

        authors_commits_history = self._squash_authors_history(authors_activity_history.commits_count,
                                                               max_authors_per_plot_count)
        authors_added_lines_history = self._squash_authors_history(authors_activity_history.insertions,
                                                                   max_authors_per_plot_count)

        # "Added lines" graph
        data = []
        for author in authors_added_lines_history:
            authorstats = {'key': author}
            series = authors_added_lines_history[author]
            authorstats['values'] = [{'x': int(x.timestamp()) * 1000, 'y': int(y)} for x, y in zip(series.index, series.values)]
            data.append(authorstats)

        lines_by_authors = {
            "data": data
        }

        # "Commit count" and streamgraph
        # TODO move the "added lines" into the same JSON to save space and download time
        data = []
        for author in authors_commits_history:
            authorstats = {'key': author}
            series = authors_commits_history[author]
            stream = series.diff().fillna(0)
            authorstats['values'] = [[int(x.timestamp() * 1000), int(y), int(z)] for x, y, z in zip(series.index, series.values, stream.values)]
            data.append(authorstats)

        commits_by_authors = {
            "data": data
        }

        email_domains_distribution = self.git_repository_statistics.domains_distribution\
            .sort_values(ascending=False)
        if self.configuration['max_domains'] < email_domains_distribution.shape[0]:
            top_domains = email_domains_distribution[:self.configuration['max_domains']]
            other_domains = email_domains_distribution[self.configuration['max_domains']:].sum()
            email_domains_distribution = top_domains.append(pd.Series(other_domains, index=["Others"]))

        from collections import OrderedDict
        email_domains_distribution = email_domains_distribution.to_dict(OrderedDict)

        # Domains
        domains = {
            "data": [{"key": domain, "y": commits_count} for domain, commits_count in email_domains_distribution.items()]
        }

        if self.git_repo_statistics.contribution:
            authors_names = self.git_repository_statistics.authors.sort().names()
            valuable_contribution = [(name, self.git_repo_statistics.contribution.get(name)) for name in authors_names
                                     if self.git_repo_statistics.contribution.get(name) is not None]

            # sort and limit to only top authors
            valuable_contribution.sort(key=lambda tup: tup[1], reverse=True)
            if len(valuable_contribution) > max_authors_per_plot_count + 1:
                rest_contributions = sum(tup[1] for tup in valuable_contribution[max_authors_per_plot_count:])
                valuable_contribution = valuable_contribution[:max_authors_per_plot_count] + [
                    ("others", rest_contributions)]
            # Contribution
            contribution = {
                "data": [{"key": name, "y": lines_count} for name, lines_count in valuable_contribution]
            }
        else:
            contribution = {}

        authors_plot = JsPlot('authors.js',
                              lines_by_authors=json.dumps(lines_by_authors),
                              commits_by_authors=json.dumps(commits_by_authors),
                              domains=json.dumps(domains),
                              contribution=json.dumps(contribution)
                              )
        return authors_plot

    def make_files_page(self):
        project_data = {
            'files_count': self.git_repo_statistics.total_files_count,
            'lines_count': self.git_repository_statistics.total_lines_count,
            'size': self.git_repo_statistics.total_tree_size,
            'files': []
        }

        for ext in sorted(self.git_repo_statistics.extensions.keys()):
            files = self.git_repo_statistics.extensions[ext]['files']
            lines = self.git_repo_statistics.extensions[ext]['lines']
            file_type_dict = {"extension": ext,
                              "count": files,
                              "lines_count": lines
                              }
            project_data['files'].append(file_type_dict)

        page = HtmlPage('Files', project=project_data)
        page.add_plot(self.make_files_plot())
        return page

    def make_files_plot(self) -> JsPlot:
        hst = self.git_repository_statistics.linear_history(self._time_sampling_interval).copy()
        hst["epoch"] = (hst.index - pd.Timestamp("1970-01-01 00:00:00+00:00")) // pd.Timedelta('1s') * 1000

        files_count_ts = hst[["epoch", 'files_count']].rename(columns={"epoch": "x", 'files_count': "y"})\
            .to_dict('records')
        lines_count_ts = hst[["epoch", 'lines_count']].rename(columns={"epoch": "x", 'lines_count': "y"})\
            .to_dict('records')
        graph_data = {
            "data": [
                {"key": "Files", "color": "#9400d3", "type": "line", "yAxis": 1, "values": files_count_ts},
                {"key": "Lines", "color": "#d30094", "type": "line", "yAxis": 2, "values": lines_count_ts},
            ]
        }

        files_plot = JsPlot('files.js', json_data=json.dumps(graph_data))
        return files_plot

    def make_tags_page(self):
        project_data = {
            'tags_count': len(self.git_repo_statistics.tags),
            'tags': []
        }

        # TODO: fix error occurring when a tag name and project name are the same
        """
        fatal: ambiguous argument 'gitstats': both revision and filename
        Use '--' to separate paths from revisions, like this:
        'git <command> [<revision>...] -- [<file>...]'
        """
        tags_sorted_by_date_desc = sort_keys_by_value_of_key(self.git_repo_statistics.tags, 'date', reverse=True)
        for tag in tags_sorted_by_date_desc:
            if 'max_recent_tags' in self.configuration \
                    and self.configuration['max_recent_tags'] <= len(project_data['tags']):
                break
            # there are tags containing no commits
            if 'authors' in self.git_repo_statistics.tags[tag].keys():
                authordict = self.git_repo_statistics.tags[tag]['authors']
                authors_by_commits = [
                    name for name, _ in sorted(authordict.items(), key=lambda kv: kv[1], reverse=True)
                ]
                authorinfo = []
                for i in reversed(authors_by_commits):
                    authorinfo.append('%s (%d)' % (i, self.git_repo_statistics.tags[tag]['authors'][i]))
                tag_dict = {
                    'name': tag,
                    'date': self.git_repo_statistics.tags[tag]['date'],
                    'commits_count': self.git_repo_statistics.tags[tag]['commits'],
                    'authors': ', '.join(authorinfo)
                }
                project_data['tags'].append(tag_dict)

        page = HtmlPage(name='Tags', project=project_data)
        return page

    def make_about_page(self):
        repostat_version = self.configuration.get_release_data_info()['develop_version']
        repostat_version_date = self.configuration.get_release_data_info()['user_version']
        page_data = {
            "version": f"{repostat_version} ({repostat_version_date})",
            "tools": [GitStatistics.get_fetching_tool_info(),
                      self.configuration.get_jinja_version()],
            "contributors": [author for author in self.configuration.get_release_data_info()['contributors']]
        }

        page = HtmlPage('About', repostat=page_data)
        return page
