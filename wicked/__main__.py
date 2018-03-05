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
import os
import subprocess
import sys
import time
import toml

from .client import config, remote, tunnel
from .host import projects


def confirm(question):
  reply = input(question + ' [N/y] ').strip().lower()
  return reply in ('y', 'yes', 'ok', 'true')


def new_project(parser, args, config_file, connect_only=False):
  """
  Creates a new project or connects the current directory to a project.
  Writes the `.wicked-project.toml` with the updated project name and
  remote information.
  """

  if os.path.isfile(config_file) and config.get('project.name', None):
    parser.error('already connected to project {!r}'.format(config.get('project.name')))

  with remote.new_client() as client:
    if connect_only:
      if not client.call(projects.project_exists, args.name):
        parser.error('project {!r} does not exist'.format(args.name))
    else:
      client.call(projects.new_project, args.name)

  if os.path.isfile(config_file):
    with open(config_file) as fp:
      cfg = toml.load(fp)
  else:
    cfg = {}
  cfg.setdefault('project', {})['name'] = args.name
  cfg.setdefault('remote', {})
  cfg['remote']['host'] = config.get('remote.host', 'localhost')
  user = config.get('remote.user', None)
  if user:
    cfg['remote']['user'] = user
  with open(config_file, 'w') as fp:
    toml.dump(cfg, fp)


def get_argument_parser(prog):
  parser = argparse.ArgumentParser(prog=prog)
  subp = parser.add_subparsers(dest='command')

  ls_command = subp.add_parser('ls', help='List all projects.')

  info_command = subp.add_parser('info', help='Show current project information.')

  tunnel_command = subp.add_parser('tunnel', help='Create a tunnel to a docker daemon.')

  new_command = subp.add_parser('new', help='Create a new project.')
  new_command.add_argument('name', help='The project name.')
  new_command.add_argument('host', nargs='?', help='The host for the project.')

  connect_command = subp.add_parser('connect', help='Connect this directory to an existing project.')
  connect_command.add_argument('name', help='The existing project\'s name.')
  connect_command.add_argument('host', nargs='?', help='The host of the project.')

  rm_command = subp.add_parser('rm', help='Delete the project.')
  rm_command.add_argument('-y', '--yes', action='store_true', help='Do not ask for confirmation.')
  rm_command.add_argument('name', nargs='?', help='The project name.')
  rm_command.add_argument('host', nargs='?', help='The host of the project.')

  return parser


def main(argv=None, prog=None):
  parser = get_argument_parser(prog)
  args = parser.parse_args(argv)

  config_file = '.wicked-project.toml'
  if os.path.isfile(config_file):
    config.read(config_file)

  if hasattr(args, 'host') and not args.host:
    args.host = remote.get_remote_display()
  if hasattr(args, 'name') and not args.name:
    args.name = config.get('project.name', None)

  if hasattr(args, 'host') and args.host:
    remote.set_remote_config(args.host)

  if args.command == 'ls':
    with remote.new_client() as client:
      for project in client.call(projects.list_projects):
        print(project)
    return 0

  elif args.command == 'info':
    name = config.get('project.name', None)
    if not name:
      parser.error('no project information')
    print('project {!r} on {}'.format(name, remote.get_remote_display()))
    return 0

  elif args.command == 'new':
    return new_project(parser, args, config_file)

  elif args.command == 'connect':
    return new_project(parser, args, config_file, connect_only=True)

  elif args.command == 'tunnel':
    with tunnel.DockerTunnel() as t:
      print('DOCKER_HOST=tcp://localhost:{}'.format(t.local_port))
      while True:
        time.sleep(0.1)
    return 0

  elif args.command == 'rm':
    if not args.name:
      parser.error('missing project name')
    with remote.new_client() as client:
      if not client.call(projects.project_exists, args.name):
        parser.error('project {!r} does not exist'.format(args.name))
      if not args.yes and not confirm('Do you really want to remove the project {!r}?'.format(args.name)):
        return 0
      client.call(projects.remove_project, args.name)
    return 0

  else:
    parser.print_usage()
    return 0


_entry_point = lambda: sys.exit(main())
