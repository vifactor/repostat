import time
import os
import csv
import datetime
from .gitstatistics import GitStatistics
from .gitstatistics import CommitDictFactory
from .reportCreator import ReportCreator


class DictionaryListCsvExporter:
    """Export dictionary values as List. Keys in dictionary doesn't exported or handled!"""

    @staticmethod
    def export(file_name: str, data: dict, append_file: bool = False, aditional_values: dict = None):
        file_mode = 'w'
        if append_file:
            file_mode = 'a'
        new_file = not os.path.isfile(file_name)

        with open(file_name, file_mode, newline='', encoding='utf-8') as csvfile:
            fieldnames = []
            data_list = []
            if aditional_values is None:
                aditional_values = {}
            is_list = type(data) is list
            if not is_list:
                fieldnames = list(data[list(data.keys())[0]].keys()) + list(aditional_values.keys())
                data_list = data.values()
            if is_list:
                fieldnames = list(data[0].keys()) + list(aditional_values.keys())
                data_list = data

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"')

            if not append_file or new_file:
                writer.writeheader()

            for line in data_list:
                tmp = dict(line)
                tmp.update(aditional_values)
                writer.writerow(tmp)
            csvfile.close()


class DictionaryCsvExporter:
    """Export dictionary values with or without keys. Able to export key-s as column!"""

    @staticmethod
    def export(file_name: str, data: dict, append_file: bool = False, export_key_as_field: bool = True,
               key_field_name: str = 'key'):
        file_mode = 'w'
        if append_file:
            file_mode = 'a'
        new_file = not os.path.isfile(file_name)

        with open(file_name, file_mode, newline='', encoding='utf-8') as csvfile:
            fieldnames = list(data[list(data.keys())[0]].keys())
            if export_key_as_field:
                fieldnames.append(key_field_name)

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"')
            if not append_file or new_file:
                writer.writeheader()

            for key, line in data.items():
                print_line = line
                if export_key_as_field:
                    print_line = dict(line)
                    print_line[key_field_name] = key
                writer.writerow(print_line)
            csvfile.close()


class CSVReportCreator(ReportCreator):

    def get_additional_fields(self, data: GitStatistics):
        return {"Project name": self.project_name,
                "Repo name": data.repo_name
                }

    def create(self, data: GitStatistics, path: str, config: dict, append_file: bool = False):

        ReportCreator.create(self, data, path, config)

        # General info
        datetime_format = '%Y-%m-%d %H:%M:%S'
        first_commit = datetime.datetime.fromtimestamp(data.first_commit_timestamp).strftime(datetime_format)
        last_commit = datetime.datetime.fromtimestamp(data.last_commit_timestamp).strftime(datetime_format)
        general_info = dict()
        general_info['1'] = {
            'Project name': self.project_name,
            'Repo name': data.repo_name,
            'Generated date': datetime.datetime.now().strftime(datetime_format),
            'Generation duration in seconds': time.time() - data.get_stamp_created(),
            'Report Period Start (First commit)': first_commit,
            'Report Period (Last commit)': last_commit,
            'Age (days)': data.get_commit_delta_days(),
            'Age (active days)': len(data.get_active_days()),
            'Total lines': data.get_total_line_count(),
            'Total lines added': data.total_lines_added,
            'Total lines removed': data.total_lines_removed,
            'Total Commits': data.get_total_commits(),
            'Authors': data.get_total_authors()
        }

        aditional_info = self.get_additional_fields(data)
        # export general info
        DictionaryCsvExporter.export(os.path.join(path, "general.csv"), general_info, append_file, False)

        # export authors
        DictionaryListCsvExporter.export(os.path.join(path, "authors.csv"), data.authors, append_file, aditional_info)

        # export commits
        DictionaryListCsvExporter.export(os.path.join(path, "commits.csv"), data.all_commits,
                                         append_file, aditional_info)

        # export total_history
        DictionaryListCsvExporter.export(os.path.join(path, "total_history.csv"), data.changes_history,
                                         append_file, aditional_info)

        ###
        # Activity

        # month of year
        lines_added_monthly = {}
        lines_removed_monthly = {}
        for oid, commit in data.all_commits.items():
            ts = commit[CommitDictFactory.TIMESTAMP]
            key = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m')
            if key in lines_added_monthly.keys():
                lines_added_monthly[key] += commit[CommitDictFactory.LINES_ADDED]
                lines_removed_monthly[key] += commit[CommitDictFactory.LINES_REMOVED]
            else:
                lines_added_monthly[key] = commit[CommitDictFactory.LINES_ADDED]
                lines_removed_monthly[key] = commit[CommitDictFactory.LINES_REMOVED]

        month_statistic = {}
        for mm in data.author_year_monthly:
            month_statistic[mm] = {
                'Project Name': self.project_name,
                'Repo name': data.repo_name,
                'Month': mm,
                'Lines added': lines_added_monthly.get(mm, 0),
                'Lines removed': lines_removed_monthly.get(mm, 0),
                'Author count': len(data.author_year_monthly.get(mm, {})),
                'Commits': data.activity_year_monthly.get(mm, 0)
            }
        DictionaryCsvExporter.export(os.path.join(path, 'activity_month_of_year.csv'), month_statistic,
                                     append_file, False)
