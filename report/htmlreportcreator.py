import os
import datetime
import calendar
import collections
import json
import math
from jinja2 import Environment, FileSystemLoader
import pandas as pd

from analysis.gitrepository import GitRepository
from tools.configuration import Configuration
from tools import packages_info

from . import colormaps
from .html_page import HtmlPage, JsPlot

HERE = os.path.dirname(os.path.abspath(__file__))


class HTMLReportCreator:
    recent_activity_period_weeks = 32
    assets_subdir = "assets"
    templates_subdir = "templates"

    def __init__(self, config: Configuration, repository: GitRepository):
        self.path = None
        self.configuration = config
        self.assets_path = os.path.join(HERE, self.assets_subdir)
        self.git_repository_statistics = repository
        self.has_tags_page = config.do_process_tags()
        self._time_sampling_interval = "W"
        self._do_generate_index_page = False
        self._is_blame_data_allowed = False
        self._max_orphaned_extensions_count = 0

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

    def allow_blame_data(self):
        self._is_blame_data_allowed = True

    def generate_index_page(self, do_generate: bool = True):
        self._do_generate_index_page = do_generate
        return self

    def set_max_orphaned_extensions_count(self, count):
        self._max_orphaned_extensions_count = count
        return self

    def _clamp_orphaned_extensions(self, extensions_df: pd.DataFrame, group_name: str = "~others~"):
        # Group together all extensions used only once (probably not really extensions)
        is_orphan = extensions_df["files_count"] <= self._max_orphaned_extensions_count
        excluded = extensions_df[is_orphan]
        print(excluded.shape)
        if excluded.shape[0] > 0:
            excluded_summary = excluded.agg({"size_bytes": ["sum"], "lines_count": ["sum", "count"]})
            orphans_summary_df = pd.DataFrame(data=[{
                "files_count": excluded_summary['lines_count']['count'],
                "lines_count": excluded_summary['lines_count']['sum'],
                "size_bytes": excluded_summary['size_bytes']['sum'].astype('int32')
            }], index=[(False, group_name)]) # index is a tuple (is_binary, extension)

            extensions_df = extensions_df[~is_orphan].sort_values(by="files_count", ascending=False)
            # and we do not sort after we appended "orphans", as we want them to appear at the end
            extensions_df = extensions_df.append(orphans_summary_df, sort=False)

        return extensions_df

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

        most_productive_authors_history.columns = most_productive_authors_history.columns.add_categories(['Others'])
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
            rendered_page = page.render(self.j2_env, linked_pages=pages)
            page.save(self.path, rendered_page)

        if self._do_generate_index_page:
            # make the landing page for a web server
            from shutil import copyfile
            copyfile(os.path.join(path, "general.html"), os.path.join(path, "index.html"))

    def make_general_page(self):
        first_commit_datetime = datetime.datetime.fromtimestamp(self.git_repository_statistics.first_commit_timestamp)
        last_commit_datetime = datetime.datetime.fromtimestamp(self.git_repository_statistics.last_commit_timestamp)

        project_data = {
            "name": self.git_repository_statistics.name,
            "branch": self.git_repository_statistics.branch,
            "age": (last_commit_datetime - first_commit_datetime).days,
            "active_days_count": self.git_repository_statistics.active_days_count,
            "commits_count": self.git_repository_statistics.total_commits_count,
            "merge_commits_count": self.git_repository_statistics.merge_commits_count,
            "authors_count": self.git_repository_statistics.authors.count(),
            "files_count": self.git_repository_statistics.head.files_count,
            "total_lines_count": self.git_repository_statistics.total_lines_count,
            "added_lines_count": self.git_repository_statistics.total_lines_added,
            "removed_lines_count": self.git_repository_statistics.total_lines_removed,
            "first_commit_date": first_commit_datetime,
            "last_commit_date": last_commit_datetime,
        }

        generation_data = {
            "datetime": datetime.datetime.today().strftime('%Y-%m-%d %H:%M')
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
        all_monthly_activity = self.git_repository_statistics.history('m')
        current_year_monthly_activity = all_monthly_activity \
            .loc[all_monthly_activity.index.year == current_year]

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

        # Commits by year/month

        # Fade out the oldest years
        alpha_step = 1.0 / len(yearly_activity.index)
        series_index = 1

        values = []
        for x in yearly_activity.index:
            year_activity = all_monthly_activity.loc[all_monthly_activity.index.year == int(x.year)]
            series = pd.Series(year_activity.values, index=year_activity.index.month)
            alpha = math.pow(alpha_step * series_index, 1.3)
            series_index = series_index + 1
            values.append({
                    'key': str(x.year),
                    'color': 'rgba(148, 00, 211, %f)' % alpha if series_index <= len(yearly_activity.index) else '#0000D3',
                    'values': [{'x': int(key) - 1, 'y': int(value)} for key, value in zip(series.index, series.values)]
            })

        by_year_month = {
            "yAxis": {"axisLabel": "Commits by month"},
            "xAxis": {"rotateLabels": -90, "ticks": 12},
            "data": values
        }

        # Review duration
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
                               commits_by_year_month=json.dumps(by_year_month),
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
            'is_blame_data_available': self._is_blame_data_allowed,
        }

        if self._is_blame_data_allowed:
            project_data.update({
                'top_knowledge_carriers': self.git_repository_statistics.head.get_top_knowledge_carriers()
                    .head(self.configuration['authors_top'])
            })

        raw_authors_data = self.git_repository_statistics.get_authors_ranking_by_month()
        ordered_months = raw_authors_data.index.get_level_values(0).unique().sort_values(ascending=False)
        project_data['months'] = []
        for yymm in ordered_months[0:self.configuration['max_authors_of_months']]:
            authors_in_month = raw_authors_data.loc[yymm]
            project_data['months'].append({
                'date': yymm,
                'top_author': {'name': authors_in_month.index[0], 'commits_count': authors_in_month.iloc[0]},
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
                'top_author': {'name': authors_in_year.index[0], 'commits_count': authors_in_year.iloc[0]},
                'next_top_authors': ', '.join(list(authors_in_year.index[1:max_top_authors_index])),
                'all_commits_count': authors_in_year.sum(),
                'total_authors_count': authors_in_year.size,
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

        if self._is_blame_data_allowed:
            # sort by contribution
            sorted_contribution = self.git_repository_statistics.head.authors_contribution.sort_values(ascending=False)
            # limit to only top authors
            if sorted_contribution.shape[0] > max_authors_per_plot_count + 1:
                rest_contributions = sorted_contribution[max_authors_per_plot_count:].sum()
                sorted_contribution = sorted_contribution[:max_authors_per_plot_count]
                # at this point index is a CategoricalIndex and without next line cannot accept new category: "others"
                sorted_contribution.index = sorted_contribution.index.to_list()
                sorted_contribution = sorted_contribution.append(pd.Series(rest_contributions, index=["others"]))
            sorted_contribution = sorted_contribution.to_dict(OrderedDict)
            # Contribution plot data
            contribution = {
                "data": [{"key": name, "y": lines_count} for name, lines_count in sorted_contribution.items()]
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
        file_ext_summary = self.git_repository_statistics.head.files_extensions_summary
        if self._max_orphaned_extensions_count > 0:
            file_ext_summary = self._clamp_orphaned_extensions(file_ext_summary)
        else:
            file_ext_summary = file_ext_summary.sort_values(by="files_count", ascending=False)

        project_data = {
            'total_files_count': self.git_repository_statistics.head.files_count,
            'total_lines_count': self.git_repository_statistics.total_lines_count,
            'size': self.git_repository_statistics.head.size,
            'file_summary': file_ext_summary,
            'is_blame_data_available': self._is_blame_data_allowed
        }
        if self._is_blame_data_allowed:
            project_data.update({
                'top_files_by_contributors_count': self.git_repository_statistics.head.get_top_files_by_contributors_count(),
                'monoauthor_files_count': self.git_repository_statistics.head.monoauthor_files.count(),
                'lost_knowledge_ratio': self.git_repository_statistics.head.get_lost_knowledge_percentage()
            })

        page = HtmlPage('Files', project=project_data)
        page.add_plot(self.make_files_plot())
        return page

    def make_files_plot(self) -> JsPlot:
        hst = self.git_repository_statistics.linear_history(self._time_sampling_interval).copy()
        hst["epoch"] = (hst.index - pd.Timestamp("1970-01-01 00:00:00+00:00")) // pd.Timedelta('1s') * 1000

        files_count_ts = hst[["epoch", 'files_count']].rename(columns={"epoch": "x", 'files_count': "y"})
        lines_count_ts = hst[["epoch", 'lines_count']].rename(columns={"epoch": "x", 'lines_count': "y"})
        maxFiles = int(files_count_ts.max()["y"])
        maxLines = int(lines_count_ts.max()["y"])
        graph_data = {
            "data": [
                {"key": "Files", "color": "#9400d3", "type": "line", "yAxis": 1, "values": files_count_ts.to_dict('records')},
                {"key": "Lines", "color": "#d30094", "type": "line", "yAxis": 2, "values": lines_count_ts.to_dict('records')},
            ],
            "maxFiles": maxFiles,
            "maxLines": maxLines
        }

        files_plot = JsPlot('files.js', json_data=json.dumps(graph_data))
        return files_plot

    def make_tags_page(self):
        if 'max_recent_tags' not in self.configuration:
            tags = list(self.git_repository_statistics.tags.all())
        else:
            tags = [next(self.git_repository_statistics.tags) for _ in range(self.configuration['max_recent_tags'])]

        project_data = {
            'tags': tags,
            # this is total tags count, generally len(tags) != total_tags_count
            'tags_count': self.git_repository_statistics.tags.count
        }

        page = HtmlPage(name='Tags', project=project_data)
        return page

    def make_about_page(self):
        repostat_version = self.configuration.get_release_data_info()['develop_version']
        repostat_version_date = self.configuration.get_release_data_info()['user_version']
        page_data = {
            "version": f"{repostat_version} ({repostat_version_date})",
            "tools": [packages_info.get_pygit2_info(),
                      packages_info.get_jinja_info()],
            "contributors": self.configuration.get_release_data_info()['contributors']
        }

        page = HtmlPage('About', repostat=page_data)
        return page
