#!/usr/bin/env python3

import sys
import os
import shutil
import gitstats
import warnings
import argparse
from tools.configuration import ReadableDir


class ExportProjectRepos:
    def __init__(self, args):
        self.project_folder = None
        self.output_folder = None
        self.tmp_output_folder = None
        self.pull_repos = False
        self.append_csv = False
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
        parser = argparse.ArgumentParser(prog="export_repos",
                                         description="Mass git repo statistic export, "
                                                     "based on project/git repo folder structure"
                                                     "Expected root folder structure: "
                                                     "root -> contain the projects"
                                                     "   | - project -> contain the repos of the project"
                                                     "       | -  gitrepo -> git repo")

        parser.add_argument("--pull_repos",
                            help="Auto execute 'git pull' command in repo folder before start statistic export",
                            action="store_true")
        parser.add_argument('--append_csv', action='store_true',
                            help="Append exists csv, instead of rewrite.")
        parser.add_argument("project_folder", action=ReadableDir, type=str, help="Folder contains project folders")
        parser.add_argument("output_folder", action=ReadableDir, type=str, help="Output folder")
        ns = parser.parse_args(args)

        self.project_folder = ns.project_folder
        self.output_folder = ns.output_folder
        self.pull_repos = ns.pull_repos
        self.append_csv = ns.append_csv
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
        if self.append_csv:
            target_dir = self.output_folder

        for project_dir in os.listdir(base_path):
            abs_dir = os.path.join(base_path, project_dir)

            if os.path.isdir(abs_dir):
                for repo_dir in os.listdir(abs_dir):
                    abs_gdir = os.path.join(abs_dir, repo_dir)
                    if os.path.isdir(abs_gdir):
                        try:
                            if not self.append_csv:
                                # create target folder if not append_csv option used
                                target_dir = self.create_project_repo_folder(project_dir, repo_dir)
                            if self.pull_repos:
                                print("Pull repo: {}".format(abs_gdir))
                                os.chdir(abs_gdir)
                                os.system("git pull")
                            # call generator export to tmp folder
                            gitstat_args = ['--output_format=csv',
                                                   format("--project_name=%s" % project_dir)]
                            if self.append_csv:
                                gitstat_args.extend(['--append_csv'])
                            gitstat_args.extend([abs_gdir, self.tmp_output_folder])

                            self._execute_gitstat(gitstat_args)
                            if not self.append_csv:
                                # move result csv from tmp folder to target dir, if not append_csv option used
                                self._move_csv(target_dir)
                        except Exception as ex:
                            warnings.warn(format("%s Project %s repo export failed!" % (project_dir, repo_dir)))
                            warnings.warn(ex)
        if self.append_csv:
            self._move_csv(target_dir)

    def run(self):
        self.before_export()
        self.export()
        self.after_export()


if __name__ == '__main__':
    export = ExportProjectRepos(sys.argv[1:])
    export.run()
