import pygit2
import jinja2


def get_pygit2_info():
    return f'{pygit2.__name__} v{pygit2.__version__} (backed by libgit2 v{pygit2.LIBGIT2_VERSION})'


def get_jinja_info():
    return f'{jinja2.__name__} v{jinja2.__version__}'
