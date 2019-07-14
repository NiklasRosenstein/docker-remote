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

import contextlib
import os
import nr.fs
import subprocess
import yaml
from . import log
from .. import config, host
from ..core import remotepy, tunnel
from ..core.subprocess import shell_call, shell_convert, shell_popen


def set_remote_config(host, user=None):
  """
  Sets the global configuration for the host and optionally the username. If
  no username is specified, it will be set to #None, thus the previous user
  setting will be overwritten.
  """

  if not user:
    user, host = host.partition('@')[::2]
    if not host:
      user, host = '', user
  config.set('remote.host', host)
  config.set('remote.user', user)


def get_remote_config():
  """
  Returns the configuration values for the remote host and username, applying
  default values.
  """

  host = config.get('remote.host', 'localhost')
  user = config.get('remote.user', None) or None
  if host != 'localhost' and not user:
    user = 'root'
  return host, user


def get_remote_string():
  """
  Returns the host and username as a single string.
  """

  host, user = get_remote_config()
  if user:
    host = '{}@{}'.format(user, host)
  return host


def create_remotepy_client(host=None, user=None, tool_name=None):
  """
  Creates a new RemotePy client for the configured host.
  """

  if host is None and user is None:
    host, user = get_remote_config()

  if host == 'localhost' and not user:
    log.info('Creating local RemotePy client.')
    return remotepy.LocalClient()
  else:
    log.info('Creating SSH RemotePy client ({}@{}).'.format(user, host))
    return remotepy.SSHClient(host, user, None, tool_name=tool_name)


def create_docker_tunnel(host=None, user=None, local_port=None,
                         remote_port=None):
  """
  Creates an SSH tunnel for the Docker daemon on the remote machine. Returns
  a #DockerTunnel instance. Note that the #DockerTunnel instance may be empty
  if no tunnel needs to be created.
  """

  if host is None and user is None:
    host, user = get_remote_config()
  if host == 'localhost' and not user:
    log.info('Skipping Docker SSH Tunnel on localhost.')
    return DockerTunnel.none()  # No tunnel required

  # TODO: Choose a random local port.
  local_port = config.get('tunnel.local_port', 2375)
  remote_port = config.get('tunnel.remote_port', '/var/run/docker.sock')
  log.info('Creating Docker SSH Tunnel {}:{} on {}@{}.'.format(
    local_port, remote_port, user, host))
  return DockerTunnel(host, user, None, local_port, remote_port)


def run_bash_script(script):
  command = ['ssh', get_remote_string(), 'bash', '-s']
  proc = shell_popen(command, stdin=subprocess.PIPE)
  proc.communicate(script.encode())
  return proc.returncode


class DockerTunnel(tunnel.SSHTunnel):

  __is_empty = False

  def __enter__(self):
    if self.__is_empty:
      return self
    return super().__enter__()

  def __exit__(self, *a):
    if self.__is_empty:
      return
    return super().__exit__(*a)

  def __bool__(self):
    return not self.__is_empty

  __nonzero__ = __bool__

  @property
  def docker_host(self):
    if self.__is_empty:
      return None
    return 'tcp://localhost:{}'.format(self.local_port)

  @classmethod
  def none(cls):
    instance = cls.__new__(cls)
    instance.__is_empty = True
    return instance


class Client:
  """
  This class wraps the docker-remote client workflow.
  """

  def __init__(self, host=None, user=None, local_port=None, remote_port=None,
               create_tunnel=None, tool_name=None):
    if create_tunnel is None:
      create_tunnel = (os.getenv('DOCKER_REMOTE_SHELL', '') != '1')
    self.host = host
    self.user = user
    self.local_port = local_port
    self.remote_port = remote_port
    self.create_tunnel = create_tunnel
    self.tool_name = tool_name or config.get('remote.remotepy', None)
    self.remote = None
    self.tunnel = None
    self._stack = None
    self._remote_path = None

  def __enter__(self):
    self._stack = contextlib.ExitStack()
    self._stack.__enter__()
    self.remote = self._stack.enter_context(create_remotepy_client(self.host, self.user, self.tool_name))
    if self.create_tunnel:
      self.tunnel = self._stack.enter_context(create_docker_tunnel(self.host, self.user, self.local_port, self.remote_port))
    if self.tunnel and self.tunnel.docker_host:
      os.environ['DOCKER_HOST'] = self.tunnel.docker_host
    return self

  def __exit__(self, *a):
    return self._stack.__exit__(*a)

  @property
  def remote_path(self):
    """
    Returns the #os.path module in used on the remote.
    """

    if self._remote_path is None:
      modname = self.remote.call(remotepy.get_module_member, 'os.path', '__name__')
      self._remote_path = __import__(modname, fromlist=[None])
    return self._remote_path

  def process_docker_compose(self, compose_config, create_volumedirs=True):
    """
    Preprocesses a docker-compose configuration. Returns a dictionary with
    the following data:

    * volume_dirs: A list of directories on the remote that must be created
      for volume mappings.

    If *create_volumedirs* is #True, volume directories will be immediately
    created.
    """

    version = compose_config.get('version')
    project_name = config.get('project.name')
    prefix = self.remote.call(host.projects.get_project_path, project_name)
    volume_dirs = []

    if not version:  # Compose file 1
      services = compose_config
    elif version.split('.')[0] in ('2', '3'):
      services = compose_config.get('services', {})
    else:
      raise RuntimeError('unknown compose file version: {!r}'.format(version))

    # Update relative volumes.
    for service in services.items():
      volumes = service[1].get('volumes', [])
      for i, volume in enumerate(volumes):
        if isinstance(volume, str):
          source = volume
          def update(x): volumes[i] = x
        elif isinstance(volume, dict):
          source = volume['source']
          def update(x): volume['source'] = x
        else:
          continue

        if ':' not in source:
          raise ValueError('invalid volume: {!r}'.format(volume))
        lv, cv = source.rpartition(':')[::2]

        # Only convert relative paths that are NOT named volumes.
        if not self.remote_path.isabs(lv) and '/' in lv:
          lv = self.remote_path.join(prefix, lv)
          update(lv + ':' + cv)

        if volume_dirs is not None:
          volume_dirs.append(lv)

    # Add dockerhost host entries.
    services = config.get('project.add_dockerhost', False)
    if services:
      ip = self.remote.call(host.dockerhost.get_docker_host_ip)
      if not ip:
        raise RuntimeError('Unable to determine Docker Host IP')
      if services is True:
        services = None
      for service in compose_config.get('services', {}).items():
        if services is None or service[0] in services:
          extra_hosts = service[1].setdefault('extra_hosts', [])
          log.info('Adding services.{}.extra_hosts: "dockerhost:{}"'.format(service[0], ip))
          extra_hosts.append('dockerhost:{}'.format(ip))

    if create_volumedirs:
      self.remote.call(host.projects.ensure_volume_dirs, project_name, volume_dirs)

    return {'volume_dirs': volume_dirs}

  def compose(self, argv, compose_config=None, preprocess=True):
    with contextlib.ExitStack() as stack:
      if compose_config is not None:
        if preprocess:
          self.process_docker_compose(compose_config)
        fp = stack.enter_context(nr.fs.tempfile('.yaml', text=True))
        fp.write(yaml.dump(compose_config))
        fp.close()
        log.debug('Final docker-compose.yml:\n\n%s', yaml.dump(compose_config))
      else:
        fp = None

      env = os.environ.copy()
      project_name = config.get('project.name')
      if not self.project_exists(project_name):
        self.new_project(project_name)

      command = ['docker-compose', '-p', project_name]
      if fp:
        command += ['-f', fp.name]
      command += ['--project-directory', '.']
      command += argv

      if os.name != 'nt' and not self.tunnel:
        command.insert(0, 'sudo')

      if os.name == 'nt' and (self.tunnel or (os.getenv('DOCKER_REMOTE_SHELL', '') == '1')):
        # Otherwise docker-compose will convert forward slashes to backward
        # slashes on Windows, even though it is actually communicating with
        # a Linux docker daemon.
        env['COMPOSE_CONVERT_WINDOWS_PATHS'] = '1'

      log.info('$ ' + shell_convert(command))
      return shell_call(command, env=env)

  def get_host_version(self):
    return self.remote.call(host.get_version)

  def list_projects(self):
    return self.remote.call(host.projects.list_projects)

  def project_exists(self, project):
    return self.remote.call(host.projects.project_exists, project)

  def new_project(self, project):
    return self.remote.call(host.projects.new_project, project)

  def remove_project(self, project):
    return self.remote.call(host.projects.remove_project, project)

  def get_project_path(self, project):
    return self.remote.call(host.projects.get_project_path, project)

  def get_volume_path(self, project, volume):
    return self.remote.call(host.projects.get_volume_path, project, volume)
