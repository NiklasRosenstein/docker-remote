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
import nr.fs
import requests
import shutil
import subprocess
import sys
import textwrap
import time
import yaml

from . import __version__, client, config
from .client import log
from .core import remotepy
from .core.subprocess import shell_call, shell_capture, shell_convert

MISSING_PROJECT_NAME = '''missing project name

You can specify the project name with the -p, --project-name option or
add it to your docker-compose.yml or docker-remote.yml:

    # docker-compose.yml            # docker-remote.yml
    version: '3'                    project:
    services: ...                     name: my_app_name
    x-docker-remote:
      project:
        name: my_app_name'''

PROJECT_DOWNLOAD_URL = 'https://github.com/NiklasRosenstein/docker-remote/archive/{ref}.zip'


def confirm(question):
  reply = input(question + ' [y/N] ').strip().lower()
  return reply in ('y', 'yes', 'ok', 'true')


def is_inside_docker_remote_shell():
  return os.getenv('DOCKER_REMOTE_SHELL') == '1'


def get_argument_parser(prog):
  parser = argparse.ArgumentParser(prog=prog)
  subparsers = parser.add_subparsers(dest='command')

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

  tunnel = subparsers.add_parser('tunnel', help='Create a tunnel to a docker daemon.')
  shell = subparsers.add_parser('shell', help='Create a tunnel and enter a new '
    'shell. Inside this shell, a docker-compose alias is created to route '
    'through docker-remote, allowing you to use your normal docker-compose '
    'workflow while having the benefits of docker-remote.')
  ls = subparsers.add_parser('ls', help='List projects on the host.')

  rm = subparsers.add_parser('rm', help='Delete a project on the host.')
  rm.add_argument('-y', '--yes', action='store_true',
    help='Do not ask for confirmation.')
  rm.add_argument('projects', nargs='*', help='Project names to delete.')

  scp = subparsers.add_parser('scp', help='Download a volume or multiple volume '
    'directories from the host. If no volumes are specified, the whole '
    'project directory is downloaded.')
  scp.add_argument('directory', help='The target directory.')
  scp.add_argument('volumes', nargs='*', help='Volume names to download.')

  docker = subparsers.add_parser('docker', help='Wrapper for docker.')
  docker.add_argument('argv', nargs='...')

  compose = subparsers.add_parser('compose', help='Wrapper for docker-compose.')
  compose.add_argument('-p', '--project-name')
  compose.add_argument('--rm', action='store_true', help='Remove the project after running.')
  compose.add_argument('argv', nargs='...')

  install = subparsers.add_parser('install', help='Install docker-remote on a host. '
    'This will run a bash script on the root user of the host specified with '
    'the -H option or the `[remote] host` configuration to install the latest '
    ' version of docker-remote via Pip (a user install). The script will '
    'also ensure that the docker-remote command-line can be found by adding '
    '$HOME/.local/bin to the PATH in .bashrc.')
  install.add_argument('--via', default='pip3', help='Name of the Pip binary '
    'to use for installation. Defaults to pip3.')
  install.add_argument('--no-current-state', action='store_true')

  info = subparsers.add_parser('info', help='Show configuration in the current context.')

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
  docker_compose_file = 'docker-compose.yml'
  if os.path.isfile(docker_compose_file):
    with open(docker_compose_file, 'r') as fp:
      docker_compose_data = yaml.safe_load(fp)
    if 'x-docker-remote' in docker_compose_data:
      config.merge(config.data, docker_compose_data['x-docker-remote'])
      # Extension fields are supported by the file format specification,
      # but apparently not by the implementation. See docker/compose#5753.
      del docker_compose_data['x-docker-remote']
  else:
    docker_compose_data = None

  if not args.host:
    args.host = client.get_remote_string()
  if not args.project_name:
    args.project_name = config.get('project.name', None)
    log.info('docker-remote project name: %s', args.project_name)
  else:
    config.set('project.name', args.project_name)

  if args.host:
    client.set_remote_config(args.host)

  if args.command == 'ls':
    with client.Client() as cl:
      for project in cl.list_projects():
        print(project)
    return 0

  elif args.command == 'rm':
    if not args.projects and not args.project_name:
      parser.error(MISSING_PROJECT_NAME)
    if not args.projects:
      args.projects = [args.project_name]

    status = 0
    with client.Client(create_tunnel=False) as cl:
      for project in (x.strip() for x in args.projects):
        if not cl.project_exists(project):
          log.error('project {!r} does not exist'.format(project))
          status = 127
          continue

        question = 'Do you really want to remove the project {!r}?'.format(project)
        if not args.yes and not confirm(question):
          continue

        try:
          cl.remove_project(project)
        except OSError as exc:
          log.error(str(exc))
          status = 127

    return 0

  elif args.command == 'docker':
    with client.Client() as cl:
      command = ['docker'] + args.argv
      log.info('$ ' + shell_convert(command))
      return shell_call(command)

  elif args.command == 'compose':
    if docker_compose_data is None:
      parser.error('file {!r} does not exist'.format(docker_compose_file))
    if not args.project_name:
      parser.error(MISSING_PROJECT_NAME)
    with client.Client() as cl:
      return cl.compose(args.argv, docker_compose_data)

  elif args.command in ('tunnel', 'shell'):
    if is_inside_docker_remote_shell():
      parser.error('It seems you are already inside a docker-remote shell.')
    is_shell = args.command == 'shell'

    with client.Client() as cl, contextlib.ExitStack() as stack:
      if is_shell:
        shell = os.getenv('SHELL', '')
        if not shell:
          shell = 'cmd' if os.name == 'nt' else 'bash'
        if 'cmd' in os.path.basename(shell) and os.name == 'nt':
          command = [shell, '/k', 'echo Setting up docker-compose alias... && echo && doskey docker-compose=docker-remote compose $*']
        else:
          tempfile = stack.enter_context(nr.fs.tempfile(text=True))
          tempfile.write('echo "Setting up docker-compose alias..."\necho\nalias docker-compose="docker-remote compose"\n')
          tempfile.close()
          command = [shell, '--rcfile', tempfile.name, '-i']

        log.info('$ ' + shell_convert(command))
        os.environ['DOCKER_REMOTE_SHELL'] = '1'
        return shell_call(command)

      elif cl.tunnel:
        print('DOCKER_HOST={}'.format(cl.tunnel.docker_host))
        while cl.tunnel.status() == 'alive':
          time.sleep(0.1)
        if cl.tunnel.status() != 'ended':
          return 1

      else:
        return 0

    assert False

  elif args.command == 'scp':
    if not args.project_name:
      parser.error(MISSING_PROJECT_NAME)

    host, user = client.get_remote_config()
    if host == 'localhost' and not user:
      host_prefix = ''
    else:
      host_prefix = '{}@{}:'.format(user, host)

    with client.Client(create_tunnel=False) as cl:
      if not cl.project_exists(args.project_name):
        parser.error('project {!r} does not exist'.format(args.project_name))

      if len(args.volumes) == 1:
        downloads = [
          (cl.get_volume_path(args.project_name, args.volumes[0]), args.directory)
        ]
      elif args.volumes:
        downloads = [
          (cl.get_volume_path(args.project_name, vol), os.path.join(args.directory, vol))
          for vol in args.volumes
        ]
      else:
        downloads = [(cl.get_project_path(args.project_name), args.directory)]

      code = 0
      for source_dir, dest_dir in downloads:
        nr.fs.makedirs(dest_dir)
        if host == 'localhost' and not user:
          command = ['cp', '-rv', source_dir, dest_dir]
          cmd = shell_convert(command)
        else:
          command1 = ['ssh', '{}@{}'.format(user, host), 'tar', '-czC', source_dir, '-f', '-', '.']
          command2 = ['tar', '-vxzC', dest_dir]
          cmd = shell_convert(command1) + ' | ' + shell_convert(command2)
        log.info('$ ' + cmd)
        code = shell_call(cmd)
        if code != 0:
          break

      return code

  elif args.command == 'install':
    host, user = client.get_remote_config()
    if host == 'localhost' and not user:
      print('No need to install docker-remote on the localhost again.')
      return 0

    commands = []

    host_archive_filename = '/tmp/docker-remote-{version}.zip'

    # Check if we're in a Git directory.
    directory = os.path.dirname(__file__)
    directory, code = shell_capture(['git', 'rev-parse', '--show-toplevel'], cwd=directory)
    if not args.no_current_state and code == 0:
      print('Collecting current repository state ...')
      ref = shell_capture(['git', 'stash', 'create'], cwd=directory, check=True)[0]
      with nr.fs.tempfile(suffix='.zip') as fp:
        fp.close()
        shell_call(['git', 'archive', '--format=zip', ref, '-o', fp.name], cwd=directory)

        description = shell_capture(['git', 'describe', '--tag'], cwd=directory)[0]
        host_archive_filename = host_archive_filename.format(version=description)

        print('Sending to host: "{}" ...'.format(host_archive_filename))
        client.send_file(fp.name, host_archive_filename)

    # Otherwise, we'll download the matching version from GitHub.
    else:
      url = PROJECT_DOWNLOAD_URL.format(ref='v' + __version__)
      print('Fetching "{}" ...'.format(url))
      with nr.fs.tempfile(suffix='.zip') as fp:
        with requests.get(url, stream=True) as resp:
          shutil.copyfileobj(resp.raw, fp)
        fp.close()

        host_archive_filename = host_archive_filename.format(version=__version__)

        print('Sending to host: "{}" ...'.format(host_archive_filename))
        client.send_file(fp.name, host_archive_filename)

    # Ensure that ~/.local/bin is in the PATH.
    commands.append(textwrap.dedent('''
      echo "$PATH" | grep "$HOME/.local/bin" >> /dev/null
      if [ $? != 0 ] ; then
        sed -e 'PATH="$HOME/.local/bin:$PATH"' -i .bashrc
        echo "Added $HOME/local/bin to .bashrc"
      fi
    ''').strip())

    # Install the package with Pip.
    commands.append('{pip} install --upgrade --user "' + host_archive_filename + '"')

    commands.append('rm "' + host_archive_filename + '"')
    commands.append('exit $?')

    script = '\n'.join(x.format(pip=args.via) for x in commands)
    return client.run_bash_script(script)

  elif args.command == 'info':
    print(yaml.dump(config.data))
    with client.Client() as cl:
      print(yaml.dump({'version': cl.get_host_version()}))

  else:
    parser.print_usage()
    return 0


_entry_point = lambda: sys.exit(main())
