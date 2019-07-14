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
"""
Subprocess tools.
"""

from __future__ import absolute_import

import os
import re
import shlex
import subprocess


def quote(s):
  """
  Enhanced implementation of #shlex.quote() as it generates single-quotes
  on Windows which can lead to problems.
  """

  if os.name == 'nt' and os.sep == '\\':
    s = s.replace('"', '\\"')
    if re.search('\s', s) or any(c in s for c in '<>'):
      s = '"' + s + '"'
  else:
    s = shlex.quote(s)
  return s


def shell_convert(command):
  if not isinstance(command, str):
    command = ' '.join(quote(x) for x in command)
  return command


def shell_popen(command, *args, **kwargs):
  kwargs['shell'] = True
  return subprocess.Popen(shell_convert(command), *args, **kwargs)


def shell_call(command, *args, **kwargs):
  kwargs['shell'] = True
  return subprocess.call(shell_convert(command), *args, **kwargs)


def shell_capture(command, *args, **kwargs):
  check = kwargs.pop('check', False)
  kwargs['stdout'] = subprocess.PIPE
  kwargs['stderr'] = subprocess.STDOUT
  proc = shell_popen(command, *args, **kwargs)
  output = proc.communicate()[0].decode()
  if check:
    if proc.returncode != 0:
      # TODO
      raise RuntimeError('exited with {}'.format(proc.returncode))
  return output.strip(), proc.returncode
