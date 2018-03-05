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

from . import config
from ..core import remotepy


def set_remote_config(host, user=None):
  if not user:
    user, host = host.partition('@')[::2]
    if not host:
      user, host = '', user
  config.set('remote.host', host)
  if user:
    config.set('remote.user', user)


def get_remote_config():
  host = config.get('remote.host', 'localhost')
  user = config.get('remote.user', None)
  if host != 'localhost' and not user:
    user = 'wicked'
  return host, user


def get_remote_display():
  host, user = get_remote_config()
  if user:
    host = '{}@{}'.format(user, host)
  return host


def new_client():
  host, user = get_remote_config()
  if host == 'localhost' and not user:
    return remotepy.LocalClient()
  else:
    return remotepy.SSHClient(host, user or 'wicked')
