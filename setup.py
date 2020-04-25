from setuptools import setup
from tools.configuration import Configuration

# name with underscore is used here because 'repostat' is already occupied by https://pypi.org/project/repostat/
setup(name='repo_stat',
      version=Configuration.get_release_data_info()['develop_version'],
      description='Desktop git repository analyser and report creator.',
      keywords='git analysis statistics vcs python',
      url='https://github.com/vifactor/repostat',
      author='Viktor Kopp',
      author_email='vifactor@gmail.com',
      license='GPLv2',
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
          "Topic :: Software Development :: Version Control",
          "Topic :: Utilities"
      ],
      python_requires='>=3.5',
      packages=['analysis', 'tools', 'report'],
      package_data={'report': ['templates/*.html',
                               'templates/*.js',
                               'assets/images/*.gif',
                               'assets/sortable.js',
                               'assets/d3.v3.min.js',
                               'assets/nv.d3.min.js',
                               'assets/nv.d3.css',
                               'assets/gitstats.css'],
                    'tools': ['release_data.json']},
      install_requires=[
          'Jinja2>=2.10.1',
          'pygit2>=1.0.3',
          'pytz>=2018.5',
          'pandas~=0.25.3'
      ],
      entry_points={"console_scripts": ["repostat = analysis.repostat:main"]},
      include_package_data=True,
      zip_safe=False)
