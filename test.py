from jinja2 import Environment, FileSystemLoader
import os
from collections import namedtuple


if __name__ == '__main__':
    # Capture our current directory
    code_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(code_dir, 'templates')

    Page = namedtuple("Page", ["link", "title"])
    j2_env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True)

    output_dir = os.path.join(code_dir, 'output')
    for template in j2_env.list_templates(filter_func=lambda template_name: template_name != 'base.html'):
        template_rendered = j2_env.get_template(template).render(
            version="abc",
            page_title=os.path.basename(template),
            text = template
        )
        print template

        rendered_file = os.path.join(output_dir, template)
        with open(rendered_file, 'w') as f:
            f.write(template_rendered)
