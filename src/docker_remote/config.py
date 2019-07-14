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

import os
import yaml

CONFIG_FILENAME = os.path.expanduser('~/.docker-remote.yml')

try:
  with open(CONFIG_FILENAME) as fp:
    data = yaml.safe_load(fp)
  del fp
except FileNotFoundError:
  data = {}


def merge(a, b):
  for key, bval in b.items():
    if isinstance(bval, dict):
      try:
        aval = a[key]
      except KeyError:
        pass
      else:
        if isinstance(aval, dict):
          bval = merge(aval, bval)
    a[key] = bval
  return a


def read(filename):
  with open(filename) as fp:
    merge(data, yaml.safe_load(fp))


def get(key, default=NotImplemented):
  parts = key.split('.')
  value = data
  for part in parts:
    try:
      if not isinstance(value, dict):
        raise KeyError
      value = value[part]
    except KeyError:
      if default is NotImplemented:
        raise KeyError(key)
      return default
  return value


def set(key, value):
  parts = key.split('.')
  target = data
  for part in parts[:-1]:
    try:
      target = target[part]
    except KeyError:
      target[part] = {}
      target = target[part]
    else:
      if not isinstance(target, dict):
        raise KeyError('can not set {!r}'.format(key))
  target[parts[-1]] = value
