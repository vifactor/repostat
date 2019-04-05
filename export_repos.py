#!/usr/bin/env python3

import sys
import os
import shutil
import gitstats
import warnings


class ExportProjectRepos:
    def __init__(self, args):
        self.project_folder = None
        self.output_folder = None
        self.tmp_output_folder = None
        self._process_params(args)

    @staticmethod
    def usage():
        print('cli usafe:  export_repos.py [root] [output folder]')
        print('Export git repos!')
        print('Expected root folder structure:')
        print('root -> contain the projects')
        print('   |- project -> contain the repos of the project')
        print('      |-  gitrepo -> git repo')
        print('')
        print('Result generated in output folder as source folders structured')
        print('project folder name will be the project_name option in getstats cli command')

    def _process_params(self, args):
        if len(args) != 3:
            self.usage()
            sys.exit(1)

        self.project_folder = args[1]
        self.output_folder = args[2]
        self.tmp_output_folder = os.path.join(self.output_folder, 'tmp')

        print("Project folder: " + self.project_folder)
        print("Output folder: " + self.output_folder)

    def _move_csv(self, target):
        # move all files from tmp folder to the target folder
        files = os.listdir(self.tmp_output_folder)

        for f in files:
            shutil.move(os.path.join(self.tmp_output_folder, f), target)

    @staticmethod
    def _execute_gitstat(args):
        gitstats.GitStats().run(args)

    def before_export(self):
        # Prepare export folder structure
        # delete output folder (after create an empty new one)
        try:
            shutil.rmtree(self.output_folder)
        except OSError as ex:
            warnings.warn(ex)

        # create the tmp output folder (inside ov target output folder, so create target output folder also)
        os.makedirs(self.tmp_output_folder)

    def after_export(self):
        # After export delete the tmp output folder. CSV Already moved to the right destination folder
        try:
            shutil.rmtree(self.tmp_output_folder)
        except OSError as ex:
            warnings.warn(ex)

    def create_project_repo_folder(self, project_name, repo_name) -> str:
        """
        Create the folder and return folder path
        :param project_name: 
        :param repo_name: 
        :return: path
        """
        result = os.path.join(self.output_folder, project_name, repo_name)
        try:
            os.makedirs(result)
        except Exception as ex:
            warnings.warn("Folder %s could not be created: %s" % (result, ex))
            raise ex
        return result

    def export(self):
        # run the export

        base_path = self.project_folder
        for project_dir in os.listdir(base_path):
            abs_dir = os.path.join(base_path, project_dir)

            if os.path.isdir(abs_dir):
                for repo_dir in os.listdir(abs_dir):
                    abs_gdir = os.path.join(abs_dir, repo_dir)
                    if os.path.isdir(abs_gdir):
                        try:
                            # create target folder
                            target_dir = self.create_project_repo_folder(project_dir, repo_dir)
                            # call generator export to tmp folder
                            self._execute_gitstat(['-coutput=csv',
                                                   format("-cproject_name=%s" % project_dir),
                                                   abs_gdir,
                                                   self.tmp_output_folder])
                            # move result csv from tmp folder to target dir
                            self._move_csv(target_dir)
                        except Exception as ex:
                            warnings.warn(format("%s Project %s repo export failed!" % (project_dir, repo_dir)))
                            warnings.warn(ex)

    def run(self):
        self.before_export()
        self.export()
        self.after_export()


if __name__ == '__main__':
    export = ExportProjectRepos(sys.argv)
    export.run()
