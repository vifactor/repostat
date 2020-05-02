import os


class HtmlPage:
    assets_path = None

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.kwargs = kwargs

    @classmethod
    def set_assets_path(cls, assets_path):
        cls.assets_path = assets_path

    def render(self, j2_env):
        print(f"Rendering '{self.name}'-page")
        # load and render template
        template_rendered = j2_env.get_template(self.name.lower() + '.html').render(
            **self.kwargs,
            page_title=self.name,
            assets_path=self.assets_path,
        )
        return template_rendered.encode('utf-8')

    def save(self, path, rendered):
        with open(os.path.join(path, self.name.lower() + ".html"), 'w', encoding='utf-8') as f:
            f.write(rendered.decode('utf-8'))
