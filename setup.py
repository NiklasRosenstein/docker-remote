
from setuptools import setup, find_packages

import io
import os
import sys


with io.open('README.md', encoding='utf8') as fp:
  readme = fp.read()


setup(
  name='docker-remote',
  version='1.0.1',
  license='MIT',
  description='Docker-remote is a wrapper for docker-compose to manage compositions on a remote machine easily.',
  long_description=readme,
  url='https://github.com/NiklasRosenstein/docker-remote',
  author='Niklas Rosenstein',
  author_email='rosensteinniklas@gmail.com',
  packages=find_packages(),
  install_requires=['nr.fs>=1.1.0', 'PyYAML>=3.12'],
  entry_points = {
    'console_scripts': [
      'docker-remote = docker_remote.__main__:_entry_point',
      'docker-remote.core.remotepy = docker_remote.core.remotepy:main'
    ]
  }
)
