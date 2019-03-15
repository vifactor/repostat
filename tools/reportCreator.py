import time
import os
from .gitstatistics import GitStatistics

class ReportCreator:
	"""Creates the actual report based on given data."""
	def __init__(self):
		self.timestamp_created = time.time()
		
	
	def create(self, data: GitStatistics, path: str, config: dict):
		self.data = data
		self.path = path
		if len(config['project_name']) == 0:
			self.projectname = os.path.basename(os.path.abspath(path))
		else:
			self.projectname = config['project_name']
		self.title = self.projectname

	def getReportCreated(self):
		return self.timestamp_created


