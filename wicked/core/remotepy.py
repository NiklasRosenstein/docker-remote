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
This module implements an interface for calling Python functions on another
machine by pickling the function to be called, its arguments and the return
value.
"""

import argparse
import paramiko
import pickle
import subprocess
import sys
import struct
import traceback

TOOL_NAME = 'wicked.core.remotepy'


class IoProtocolHandler:
  """
  This class uses a binary communication protocol over stdin/stdout.
  """

  def __init__(self, stdin=None, stdout=None, log_exception=True):
    self.stdin = stdin or sys.stdin.buffer
    self.stdout = stdout or sys.stdout.buffer
    self.log_exception = log_exception

  def handle_request(self):
    object_size = self.stdin.read(4)
    if not object_size:
      return False  # End of stream
    try:
      object_size = struct.unpack('!I', object_size)[0]
      data = pickle.loads(self.stdin.read(object_size))
      response = data['function'](*data['args'], **data['kwargs'])
      response = ('return', response)
    except BaseException as exc:
      if self.log_exception:
        traceback.print_exc()
      response = ('exception', exc)
    try:
      response = pickle.dumps(response)
    except BaseException as exc:
      if self.log_exception:
        traceback.print_exc()
      # This should *really* be picklable..
      response = pickle.dumps(('exception', exc))
    self.stdout.write(struct.pack('!I', len(response)))
    self.stdout.write(response)
    self.stdout.flush()
    return True


class IoProtocolClient:
  """
  This class enables communication with the #IoProtocolHandler backend.
  """

  def __init__(self, fwrite, fread):
    self.fwrite = fwrite
    self.fread = fread

  def call(self, __func, *args, **kwargs):
    request = {'function': __func, 'args': args, 'kwargs': kwargs}
    request = pickle.dumps(request)
    self.fwrite.write(struct.pack('!I', len(request)))
    self.fwrite.write(request)
    self.fwrite.flush()
    response_size = struct.unpack('!I', self.fread.read(4))[0]
    type_, data = pickle.loads(self.fread.read(response_size))
    if type_ == 'return':
      return data
    elif type_ == 'exception':
      raise data
    else:
      raise RuntimeError('protocol error, unknown result type {!r}'.format(type_))


class SSHClient:
  """
  A client that runs this module on the remote via SSH.
  """

  def __init__(self, host, username=None, password=None):
    self.host = host
    self.username = username
    self.password = password

  def __enter__(self):
    self._ssh = paramiko.SSHClient()
    self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    self._ssh.connect(self.host, username=self.username, password=self.password)
    command = [TOOL_NAME, '--ioproto']
    stdin, stdout, stderr = self._ssh.exec_command(command)
    stderr.close()
    self._pipes = (stdin, stdout)
    self._client = IoProtocolClient(stdin, stdout)
    return self

  def __exit__(self, *a):
    [x.close() for x in self._pipes]
    self._ssh.close()

  def call(self, *args, **kwargs):
    return self._client.call(*args, **kwargs)


class LocalClient:
  """
  A client that runs this module on the same machine in another process.
  """

  def __enter__(self):
    command = [TOOL_NAME, '--ioproto']
    self._proc = subprocess.Popen(command, stdin=subprocess.PIPE,
      stdout=subprocess.PIPE, shell=True)
    self._client = IoProtocolClient(self._proc.stdin, self._proc.stdout)
    return self

  def __exit__(self, *a):
    self._proc.stdin.close()
    self._proc.stdout.close()
    self._proc.wait()

  def call(self, *args, **kwargs):
    return self._client.call(*args, **kwargs)


def get_module_member(module_name, member):
  module = __import__(module_name, fromlist=[None])
  return getattr(module, member)


def main(argv=None, prog=None):
  parser = argparse.ArgumentParser(prog=prog, add_help=False)
  parser.add_argument('--ioproto', action='store_true',
    help='Create an IoProtocolHandler that handles requests until the '
         'standard input stream is closed. As a client, you can use the '
         'IoProtocolClient or more convenient SSHClient or LocalClient '
         'classes to communicate with the process.')
  args = parser.parse_args(argv)

  if args.ioproto:
    handler = IoProtocolHandler()
    while handler.handle_request():
      pass
  else:
    parser.print_help()


if __name__ == '__main__':
  main()
