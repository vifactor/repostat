from jinja2 import Environment, FileSystemLoader
import os
from collections import namedtuple
import datetime
import dateutils

project_data = {
    "name": "Repostat",
    "url": "https://github.com/vifactor/repostat",
    "version": "X.Y.Z",
    "tools": ["python v.X", "git v.Y", "gnuplot v.Z"],
    "age": 456,
    "active_days_count": 11,
    "active_days_ratio": "{0:.2f}".format(float(11) / 456 * 100),
    "commits_count": 100,
    "commits_per_active_day_count": "{0:.2f}".format(float(100) / 11),
    "commits_per_day_count": "{0:.2f}".format(float(100) / 456),
    "authors_count": 30,
    "commits_per_author_count": "{0:.2f}".format(float(100) / 30),
    "files_count": 128,
    "total_lines_count": 1204,
    "added_lines_count": 5032,
    "removed_lines_count": 5032 - 1024,
    "first_commit_date": datetime.datetime.today() - dateutils.relativedelta(months=13),
    "last_commit_date": datetime.datetime.today() - dateutils.relativedelta(months=2, days=5)
    }

generation_data = {
    "datetime": datetime.datetime.today(),
    "duration": 10
}

if __name__ == '__main__':
    # Capture our current directory
    code_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(code_dir, 'templates')

    Page = namedtuple("Page", ["link", "title"])
    j2_env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True)

    output_dir = os.path.join(code_dir, 'output')
    for template in j2_env.list_templates(filter_func=lambda template_name: template_name != 'base.html'):
        template_rendered = j2_env.get_template(template).render(
            project=project_data,
            generation=generation_data
        )
        print template

        rendered_file = os.path.join(output_dir, template)
        with open(rendered_file, 'w') as f:
            f.write(template_rendered)
