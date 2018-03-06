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

import argparse
import contextlib
import os
import nr.tempfile
import subprocess
import sys
import time
import toml
import yaml

from . import config, __version__
from .core import remotepy
from .core.subp import shell_convert, shell_call
from .utils.namegen import namegen
from .client import dockertunnel, dockercompose, log, remote
from .host import projects

MISSING_PROJECT_NAME = '''missing project name

You can specify the project name with the -p, --project-name option or
add it to your docker-compose.yml or docker-remote.toml:

    # docker-compose.yml            # docker-remote.toml
    version: '3'                    [project]
    services: ...                   name = "my_app_name"
    x-docker-remote:
      project:
        name: my_app_name'''


def confirm(question):
  reply = input(question + ' [y/N] ').strip().lower()
  return reply in ('y', 'yes', 'ok', 'true')


def get_argument_parser(prog):
  parser = argparse.ArgumentParser(prog=prog)
  subp = parser.add_subparsers(dest='command')

  # General options.
  parser.add_argument('--version', action='version', version=__version__)
  parser.add_argument('-p', '--project-name', help='The project name. If '
    'this option is omitted, it will be read from the configuration file.')
  parser.add_argument('-H', '--host', help='The name of the Docker host. '
    'If this option is omitted, it will be read from the configuration file '
    'or fall back on "localhost". In the case of "localhost", no SSH tunnel '
    'will be created. This option may include the user in the form of '
    '"user@host".')
  parser.add_argument('-v', '--verbose', action='count', default=0,
    help='Generate more output, such as sub-commands that are being invoked.')

  tunnel = subp.add_parser('tunnel', help='Create a tunnel to a docker daemon.')
  shell = subp.add_parser('shell', help='Create a tunnel and enter a new '
    'shell. Inside this shell, a docker-compose alias is created to route '
    'through docker-remote, allowing you to use your normal docker-compose '
    'workflow while having the benefits of docker-remote.')
  ls = subp.add_parser('ls', help='List projects on the host.')

  rm = subp.add_parser('rm', help='Delete a project on the host.')
  rm.add_argument('-y', '--yes', action='store_true',
    help='Do not ask for confirmation.')
  rm.add_argument('projects', nargs='*', help='Project names to delete.')

  scp = subp.add_parser('scp', help='Download a volume or multiple volume '
    'directories from the host. If no volumes are specified, the whole '
    'project directory is downloaded.')
  scp.add_argument('directory', help='The target directory.')
  scp.add_argument('volumes', nargs='*', help='Volume names to download.')

  docker = subp.add_parser('docker', help='Wrapper for docker.')
  docker.add_argument('argv', nargs='...')

  compose = subp.add_parser('compose', help='Wrapper for docker compose.')
  compose.add_argument('-p', '--project-name')
  compose.add_argument('--rm', action='store_true', help='Remove the project after running.')
  compose.add_argument('argv', nargs='...')

  return parser


def main(argv=None, prog=None):
  parser = get_argument_parser(prog)
  args = parser.parse_args(argv)

  # Init logging.
  if args.verbose > 1:
    log.logger.setLevel(log.logging.INFO)
  elif args.verbose > 0:
    log.logger.setLevel(log.logging.DEBUG)

  # Read the local configuration file.
  config_file = 'docker-remote.toml'
  if os.path.isfile(config_file):
    config.read(config_file)
  docker_compose_file = 'docker-compose.yml'
  if os.path.isfile(docker_compose_file):
    with open(docker_compose_file, 'r') as fp:
      docker_compose_data = yaml.load(fp)
    if 'x-docker-remote' in docker_compose_data:
      config.merge(config.data, docker_compose_data['x-docker-remote'])
      # Extension fields are supported by the file format specification,
      # but apparently not by the implementation. See docker/compose#5753.
      del docker_compose_data['x-docker-remote']
  else:
    docker_compose_data = None

  if not args.host:
    args.host = remote.get_remote_display()
  if not args.project_name:
    args.project_name = config.get('project.name', None)

  if args.host:
    remote.set_remote_config(args.host)

  if args.command == 'ls':
    with remote.new_client() as client:
      for project in client.call(projects.list_projects):
        print(project)
    return 0

  elif args.command in ('tunnel', 'shell'):
    if os.getenv('DOCKER_REMOTE_SHELL') == '1':
      parser.error('It seems you are already inside a docker-remote shell.')
    is_shell = args.command == 'shell'
    with dockertunnel.new_tunnel() as (tun, docker_host), contextlib.ExitStack() as stack:
      if is_shell:
        os.environ['DOCKER_HOST'] = docker_host
        shell = os.getenv('SHELL', '')
        if not shell:
          shell = 'cmd' if os.name == 'nt' else 'bash'
        if 'cmd' in os.path.basename(shell) and os.name == 'nt':
          command = [shell, '/k', 'echo Setting up docker-compose alias... && doskey docker-compose=docker-remote compose $*']
        else:
          tempfile = stack.enter_context(nr.tempfile.tempfile(text=True))
          tempfile.write('echo "Setting up docker-compose alias..."\nalias docker-compose="docker-remote compose"\n')
          tempfile.close()
          command = [shell, '--rcfile', tempfile.name, '-i']
        log.info('$ ' + shell_convert(command))
        os.environ['DOCKER_REMOTE_SHELL'] = '1'
        return subprocess.call(command)
      else:
        print('DOCKER_HOST={}'.format(docker_host))
        while tun.status() == 'alive':
          time.sleep(0.1)
        if tun.status() != 'ended':
          return 1
    assert False

  elif args.command == 'rm':
    if not args.projects:
      if not args.project_name:
        parser.error(MISSING_PROJECT_NAME)
      args.projects = [args.project_name]
    with remote.new_client() as client:
      for project in args.projects:
        project = project.strip()
        if not client.call(projects.project_exists, project):
          parser.error('project {!r} does not exist'.format(project))
        if not args.yes and not confirm('Do you really want to remove the project {!r}?'.format(project)):
          return 0
        client.call(projects.remove_project, project)
    return 0

  elif args.command == 'docker':
    with dockertunnel.new_tunnel() as (tun, docker_host):
      os.environ['DOCKER_HOST'] = docker_host
      return shell_call(['docker'] + args.argv)

  elif args.command == 'compose':
    with contextlib.ExitStack() as stack:
      client = stack.enter_context(remote.new_client())

      if not args.project_name:
        parser.error(MISSING_PROJECT_NAME)

      if args.rm:
        stack.callback(client.call, projects.remove_project, args.project_name)

      if docker_compose_data is None:
        parser.error('file {!r} does not exist'.format(docker_compose_file))

      try:
        try:
          client.call(projects.new_project, args.project_name)
        except projects.AlreadyExists:
          pass

        prefix = client.call(projects.get_project_path, args.project_name)
        volume_dirs = []
        path_module = client.call(remotepy.get_module_member, 'os.path', '__name__')
        path_module = __import__(path_module, fromlist=[None])
        docker_compose_data = dockercompose.prefix_volumes(path_module, docker_compose_data, prefix, volume_dirs)
        client.call(projects.ensure_volume_dirs, args.project_name, volume_dirs)

        host, user = remote.get_remote_config()
        if host == 'localhost' and not user:
          pass
        else:
          tun, docker_host = stack.enter_context(dockertunnel.new_tunnel())
          os.environ['DOCKER_HOST'] = docker_host

        code = dockercompose.run(args.argv, args.project_name, docker_compose_data)
        success = (code == 0)
      except KeyboardInterrupt:
        pass

  elif args.command == 'scp':
    if not args.project_name:
      parser.error(MISSING_PROJECT_NAME)
    cfg = dockertunnel.get_ssh_config()
    if cfg['host'] == 'localhost':
      host_prefix = ''
    else:
      host_prefix = '{user}@{host}:'.format(**cfg)
    with remote.new_client() as client:
      if not client.call(projects.project_exists, args.project_name):
        parser.error('project {!r} does not exist'.format(args.project_name))
      command = ['scp', '-r']
      if args.volumes:
        for volume in args.volumes:
          volpath = client.call(projects.get_volume_path, args.project_name, volume)
          command.append(host_prefix + volpath)
      else:
        projpath = client.call(projects.get_project_path, args.project_name)
        command.append(host_prefix + projpath)
      command.append(args.directory)
    log.info('$ ' + shell_convert(command))
    return shell_call(command)

  else:
    parser.print_usage()
    return 0


_entry_point = lambda: sys.exit(main())
