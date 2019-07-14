# -*- coding: utf8 -*-
# Copyright (c) 2019 Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

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
