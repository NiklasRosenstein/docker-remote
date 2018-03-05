# The MIT License (MIT)
#
# Copyright (c) 2018 Niklas Rosenstein
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
"""
This module provides an API for querying project information on the current
machine.
"""

import filelock
import os
import nr.path
import re
import shutil

from . import config

METADATA_FILE = '.wicked-project'
PROJECT_ROOT = os.path.expanduser(config.get('host.project_root', '~'))


class ProjectError(Exception):
  pass


class AlreadyExists(ProjectError):
  pass


class DoesNotExist(ProjectError):
  pass


def _makedir(path):
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST:
      pass
    raise


def get_project_path(name):
  return os.path.normpath(os.path.join(PROJECT_ROOT, name))


def project_lock(name, metadata_file=None):
  if metadata_file is None:
    metadata_file = os.path.join(PROJECT_ROOT, name, METADATA_FILE)
  if not os.path.isfile(metadata_file):
    raise DoesNotExist(name)
  return filelock.FileLock(metadata_file + '.lock')


def project_exists(name):
  return os.path.isfile(os.path.join(get_project_path(name), METADATA_FILE))


def list_projects():
  if not os.path.isdir(PROJECT_ROOT):
    return []
  result = []
  for name in os.listdir(PROJECT_ROOT):
    path = os.path.join(PROJECT_ROOT, name)
    metadata_file = os.path.join(path, METADATA_FILE)
    if os.path.isfile(metadata_file):
      result.append(name)
  return result


def new_project(name):
  if not re.match('^[\w\d\-\_\.]+$', name):
    raise ValueError('invalid project name: {!r}'.format(name))
  project_path = get_project_path(name)
  metadata_file = os.path.join(project_path, METADATA_FILE)
  if os.path.isfile(metadata_file):
    raise AlreadyExists(name)
  _makedir(project_path)
  with open(metadata_file, 'w') as fp:
    fp.write('{}')


def remove_project(name):
  project_path = get_project_path(name)
  metadata_file = os.path.join(project_path, METADATA_FILE)
  if not os.path.isfile(metadata_file):
    raise DoesNotExist(name)
  # TODO: Check if containers are still running in this project and
  #       prevent deletion of the project until they are stopped.
  shutil.rmtree(project_path)


def ensure_volume_dirs(name, dirs):
  project_path = get_project_path(name)
  for dirname in dirs:
    if not os.path.isabs(dirname):
      dirname = os.path.join(project_path, dirname)
    nr.path.makedirs(dirname)
