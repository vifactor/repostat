import sys
import os
import argparse


class ReadableDir(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = os.path.abspath(os.path.expanduser(values))
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("Path {0} is not valid.".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError("Directory {0} is not readable.".format(prospective_dir))


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(prog='ReportChecker',
                                        description="Checks presence of all expected repostat's report files")
    argparser.add_argument('--is-relocatable', action="store_true", help="Is generated report relocatable")
    argparser.add_argument('--has-index-page', action="store_true", help="Report is generated with index.html")
    argparser.add_argument('report_path', type=str, action=ReadableDir, help="Path to generated report")
    parsed_args = argparser.parse_args(sys.argv[1:])

    expected_files = [
        "about.html",
        "activity.html",
        "activity.js",
        "authors.html",
        "authors.js",
        "files.html",
        "files.js",
        "general.html",
        "tags.html"
    ]

    if parsed_args.has_index_page:
        expected_files.append("index.html")

    # relocatable report has asset files in its dir
    if parsed_args.is_relocatable:
        expected_asset_files = [
            "d3.v3.min.js",
            "gitstats.css",
            os.path.join("images", "arrow-down.gif"),
            os.path.join("images", "arrow-none.gif"),
            os.path.join("images", "arrow-up.gif"),
            "nv.d3.css",
            "nv.d3.min.js",
            "sortable.js",
        ]
        expected_files.extend(os.path.join("assets", asset_file) for asset_file in expected_asset_files)

    existence_check_result = [os.path.exists(os.path.join(parsed_args.report_path, asset_file))
                              for asset_file in expected_files]
    if not all(existence_check_result):
        ifile_not_found = existence_check_result.index(False)
        print(f"File '{expected_files[ifile_not_found]}' has not been found.")
        sys.exit(1)

    print("All good!")
