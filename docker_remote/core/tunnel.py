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
Create an SSH tunnel via the `ssh` client program.
"""

import subprocess
import time


class SSHTunnel:

  def __init__(self, local_port, remote_port, host, user=None):
    self.local_port = local_port
    self.remote_port = remote_port
    self.host = host
    self.user = user

  def __repr__(self):
    return 'SSHTunnel({!r})'.format(self.ssh_command())

  def __enter__(self):
    self._proc = subprocess.Popen(self.ssh_command())
    return self

  def __exit__(self, *a):
    self._proc.terminate()
    self._proc.wait()

  def ssh_command(self):
    mapping = '{}:{}'.format(self.local_port, self.remote_port)
    host = self.host
    if self.user:
      host = '{}@{}'.format(self.user, host)
    return ['ssh', '-NL', mapping, host]

  def status(self):
    code = self._proc.poll()
    if code is None:
      return 'alive'
    elif code == 0:
      return 'ended'
    else:
      return 'error'
