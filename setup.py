
from setuptools import setup, find_packages

import io
import os
import re
import sys


with io.open('README.md', encoding='utf8') as fp:
  readme = fp.read()


with io.open('src/docker_remote/__init__.py') as fp:
  version = re.search(r'__version__\s*=\s*\'(.*)\'', fp.read()).group(1)
  assert re.match(r'\d+\.\d+\.\d+', version)


setup(
  name='docker-remote',
  version=version,
  license='MIT',
  description='Docker-remote is a wrapper for docker-compose to manage compositions on a remote machine easily.',
  long_description=readme,
  url='https://github.com/NiklasRosenstein/docker-remote',
  author='Niklas Rosenstein',
  author_email='rosensteinniklas@gmail.com',
  packages=find_packages('src'),
  package_dir={'': 'src'},
  install_requires=['nr.fs>=1.1.0', 'PyYAML>=3.12', 'requests'],
  entry_points = {
    'console_scripts': [
      'docker-remote = docker_remote.__main__:_entry_point',
      'docker-remote.core.remotepy = docker_remote.core.remotepy:main'
    ]
  }
)
