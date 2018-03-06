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

import os
import nr.tempfile
import posixpath
import yaml
from . import log
from ..core.subp import shell_convert, shell_call


def prefix_volumes(path_module, config, prefix, volume_dirs=None):
  for service in config.get('services', {}).items():
    volumes = service[1].get('volumes', [])
    for i, volume in enumerate(volumes):
      if ':' not in volume:
        raise ValueError('invalid volume: {!r}'.format(volume))
      lv, cv = volume.rpartition(':')[::2]
      if not path_module.isabs(lv):
        lv = path_module.join(prefix, lv)
        volumes[i] = lv + ':' + cv
      if volume_dirs is not None:
        volume_dirs.append(lv)
  return config


def run(argv, project_name, config=None):
  with nr.tempfile.tempfile(suffix='.yaml', text=True) as temp_config:
    if config:
      temp_config.write(yaml.dump(config))
    temp_config.close()
    command = ['docker-compose', '-p', project_name]
    if config:
      log.info(yaml.dump(config))
      command += ['-f', temp_config.name]
    command += ['--project-directory', '.']
    command += argv
    if os.name != 'nt' and not os.getenv('DOCKER_HOST'):
      command.insert(0, 'sudo')
    log.info('$ ' + shell_convert(command))
    return shell_call(command)
