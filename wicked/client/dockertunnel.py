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

import contextlib
from . import log, remote
from .. import config
from ..core import tunnel


def get_ssh_config():
  # TODO: Choose a random available port?
  local_port = config.get('tunnel.local_port', 2375)
  remote_port = config.get('tunnel.remote_port', '/var/run/docker.sock')
  host = remote.get_remote_config()[0]
  user = config.get('tunnel.remote_user', None) or 'root'
  return {'local_port': local_port, 'remote_port': remote_port,
          'host': host, 'user': user}


@contextlib.contextmanager
def new_tunnel():
  """
  Creates a tunnel to a docker daemon on another machine via SSH per the
  configuration.
  """

  cfg = get_ssh_config()
  with tunnel.SSHTunnel(cfg['local_port'], cfg['remote_port'], cfg['host'], cfg['user']) as tun:
    log.info('Creating tunnel [{local_port}] ==> [{user}@{host}:{remote_port}]...'.format(**cfg))
    yield tun, 'tcp://localhost:{}'.format(local_port)
