import os


class JsPlot:
    def __init__(self, template_filename, **kwargs):
        self.template_filename = template_filename
        self.kwargs = kwargs

    def bootstrap(self, j2_env):
        bootstrapped = j2_env.get_template(self.template_filename).render(
            **self.kwargs,
        )
        return bootstrapped

    @property
    def filename(self):
        # property used for readability and in case in future jinja template name becomes different from
        # rendered filename
        return self.template_filename

    def save(self, path, bootstrapped_js):
        with open(os.path.join(path, self.filename), 'w') as fg:
            fg.write(bootstrapped_js)


class HtmlPage:
    assets_path = None

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.is_active = False
        self.kwargs = kwargs
        self._plots = []
        self._bootstrapped_plots = []

    @classmethod
    def set_assets_path(cls, assets_path):
        cls.assets_path = assets_path

    @property
    def filename(self):
        return self.name.lower() + '.html'

    @property
    def template_name(self):
        return self.name.lower() + '.html'

    def add_plot(self, plot: JsPlot):
        self._plots.append(plot)

    def render(self, j2_env, linked_pages):
        print(f"Rendering '{self.name}'-page")

        # linked_pages contain reference to this page as well
        # the following sets currently rendered page as active to apply appropriate css style in navigation bar
        self.is_active = True
        # load and render template
        template_rendered = j2_env.get_template(self.template_name).render(
            **self.kwargs,
            page_title=self.name,
            pages=linked_pages,
            assets_path=self.assets_path,
        )
        self.is_active = False

        # also bootstrap all page's plots
        for p in self._plots:
            self._bootstrapped_plots.append(p.bootstrap(j2_env))

        return template_rendered.encode('utf-8')

    def save(self, path, rendered):
        # save all plots
        for p, bp in zip(self._plots, self._bootstrapped_plots):
            p.save(path, bp)

        # and the htm itself
        with open(os.path.join(path, self.filename), 'w', encoding='utf-8') as f:
            f.write(rendered.decode('utf-8'))

