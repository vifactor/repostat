from .gitdata import RevisionData


class GitRevision:
    def __init__(self, raw_revision_data: RevisionData):
        self.revision_df = raw_revision_data.as_dataframe()

    @property
    def authors_contribution(self):
        return self.revision_df[["committer_name", "lines_count"]]\
            .groupby(by="committer_name")["lines_count"].sum()
