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
Creates an SSH tunnel to the docker daemon on another machine.
"""

import subprocess
from . import config, remote


class SSHTunnel:
  """
  Base class for SSH tunnels.
  """

  def __init__(self, local_port, remote_port, host, user=None):
    self.local_port = local_port
    self.remote_port = remote_port
    self.host = host
    self.user = user

  def __enter__(self):
    mapping = '{}:{}'.format(self.local_port, self.remote_port)
    host = '{}@{}'.format(self.user or 'root', self.host)
    command = ['ssh', '-NL', mapping, self.host]
    self._proc = subprocess.Popen(command)

  def __exit__(self, *a):
    self._proc.terminate()
    self._proc.wait()


class DockerTunnel:

  def __init__(self, local_port=None):
    if local_port is None:
      # TODO: Maybe just choose a random local port.
      local_port = config.get('tunnel.local_port', 2375)
    remote_port = config.get('tunnel.remote_port', '/var/run/docker.sock')
    user = config.get('tunnel.remote_user', None)
    host = remote.get_remote_config()[0]
    self.local_port = local_port
    self.remote_port = remote_port
    self.host = host
    self.user = user
    self._tunnel = SSHTunnel(local_port, remote_port, host, user)

  def __enter__(self):
    self._tunnel.__enter__()
    return self

  def __exit__(self, *a):
    return self._tunnel.__exit__(*a)
