from setuptools import setup
from tools.configuration import Configuration

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt', "r") as req_file:
    requirements = req_file.read().splitlines()

# such name for package is used here because 'repostat' is already occupied by https://pypi.org/project/repostat/
setup(name='repostat-app',
      version=Configuration.get_release_data_info()['develop_version'],
      description='Desktop git repository analyser and report creator.',
      keywords='git analysis statistics vcs python visualization',
      url='https://github.com/vifactor/repostat',
      author='Viktor Kopp',
      author_email='vifactor@gmail.com',
      license='GPLv3',
      long_description=long_description,
      long_description_content_type="text/markdown",
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Intended Audience :: Developers",
          "Intended Audience :: Science/Research",
          "Intended Audience :: Education",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
          "Topic :: Software Development :: Version Control",
          "Topic :: Utilities",
          "Operating System :: OS Independent",
          "Operating System :: POSIX",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: Microsoft :: Windows",
      ],
      python_requires='>3.5',
      packages=['analysis', 'tools', 'report'],
      package_data={'report': ['templates/*.html',
                               'templates/*.js',
                               'assets/images/*.gif',
                               'assets/*.js',
                               'assets/*.css'],
                    'tools': ['release_data.json']},
      install_requires=requirements,
      entry_points={"console_scripts": ["repostat = analysis.repostat:main"]},
      include_package_data=True,
      zip_safe=False)
