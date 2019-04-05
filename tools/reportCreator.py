import time
from .gitstatistics import GitStatistics


class ReportCreator:
    """Creates the actual report based on given data."""

    def __init__(self):
        self.timestamp_created = time.time()
        self.path = ""
        self.data: GitStatistics = None
        self.project_name = ""
        self.title = ""

    def create(self, data: GitStatistics, path: str, config: dict):
        self.data = data
        self.path = path
        if len(config['project_name']) == 0:
            self.project_name = data.repo_name
        else:
            self.project_name = config['project_name']
        self.title = self.project_name

    def get_report_created(self):
        return self.timestamp_created
