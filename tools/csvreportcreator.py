import time
import os
import csv
import datetime
from .gitstatistics  import GitStatistics
from .gitstatistics  import CommitDictFactory
from .reportCreator import ReportCreator


class DictionaryListCsvExporter():
	"""Export dictionary values as List. Keys in dictionary doesn't exported or handled!"""

	@staticmethod
	def export(fileName: str, data: dict, aditionalValues: dict = None):
		with open(fileName, 'w', newline='') as csvfile:
			fieldnames = []
			dataList = []
			if aditionalValues == None:
				aditionalValues = {}
			is_list = type(data) is list
			if not is_list:
				fieldnames = list(data[list(data.keys())[0]].keys()) + list(aditionalValues.keys())
				dataList = data.values()
			if is_list:
				fieldnames = list(data[0].keys()) + list(aditionalValues.keys())
				dataList = data

			writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"')
			
			writer.writeheader()
			
			for line in dataList:
				tmp = dict(line)
				tmp.update(aditionalValues)
				writer.writerow(tmp)
			csvfile.close()

class DictionaryCsvExporter():
	"""Export dictionary values with or without keys. Able to export key-s as column!"""
	
	@staticmethod
	def export(fileName: str, data: dict, exportKeyAsField: bool = True, keyFieldName: str = 'key'):
		with open(fileName, 'w', newline='') as csvfile:
			fieldnames = list(data[list(data.keys())[0]].keys())
			if exportKeyAsField:
				fieldnames.append(keyFieldName)

			writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"')
			
			writer.writeheader()
			for key, line in data.items():
				print_line = line
				if exportKeyAsField:
					print_line = dict(line)
					print_line[keyFieldName] = key
				writer.writerow(print_line)
			csvfile.close()

class CSVReportCreator(ReportCreator):
	def printHeader(self, f):
		return
	def printNav(self, f):
		return
	
	
	def getAdditionalFields(self, data: GitStatistics):
		return {"Project name": self.projectname,
			"Repo name": data.reponame}

	def create(self, data: GitStatistics, path: str, config: dict):
		
		ReportCreator.create(self, data, path, config)

		#General info
		format = '%Y-%m-%d %H:%M:%S'
		first_commit = datetime.datetime.fromtimestamp(data.first_commit_timestamp).strftime(format)
		last_commit = datetime.datetime.fromtimestamp(data.last_commit_timestamp).strftime(format)
		generalInfo = {}
		generalInfo['1'] ={
			'Project name': self.projectname,
			'Repo name': data.reponame,
			'Generated date': datetime.datetime.now().strftime(format),
			'Generation duration in seconds': time.time() - data.getStampCreated(), 
			'Report Period Start (First commit)': first_commit,
			'Report Period (Last commit)': last_commit,
			'Age (days)': data.getCommitDeltaDays(),
			'Age (active days)': len(data.getActiveDays()),
			'Total lines': data.getTotalLineCount(),
			'Total lines added': data.total_lines_added,
			'Total lines removed': data.total_lines_removed,
			'Total Commits': data.getTotalCommits(),
			'Authors': data.getTotalAuthors()
		}

		aditionalInfo = self.getAdditionalFields(data)
		#export general info
		DictionaryCsvExporter.export(os.path.join(path, "general.csv"), generalInfo, False)

		#export authors
		DictionaryListCsvExporter.export(os.path.join(path, "authors.csv"), data.authors, aditionalInfo)

		#export commits
		DictionaryListCsvExporter.export(os.path.join(path, "commits.csv"), data.commits, aditionalInfo)

		###
		# Activity
		
		#month of year
		linesAddedMonthly = data.get_lines_insertions_by_month()
		linesRemovedMonthly = data.get_lines_deletions_by_month()
		monthStatistic = {}
		for mm in data.author_year_monthly:
			monthStatistic[mm]={
				'Project Name': self.projectname,
				'Repo name': data.reponame,
				'Month': mm,
				'Lines added': linesAddedMonthly.get(mm, 0),
				'Lines removed': linesRemovedMonthly.get(mm, 0),
				'Author count': len(data.author_year_monthly.get(mm, {})),
				'Commits': data.activity_year_monthly.get(mm, 0)
			}
		DictionaryCsvExporter.export(path + '/activity_month_of_year.csv', monthStatistic, False)

