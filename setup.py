
import os
import sys
from setuptools import setup, find_packages

def readme():
  if os.path.isfile('README.md') and any('dist' in x for x in sys.argv[1:]):
    if os.system('pandoc -s README.md -o README.rst') != 0:
      print('-----------------------------------------------------------------')
      print('WARNING: README.rst could not be generated, pandoc command failed')
      print('-----------------------------------------------------------------')
      if sys.stdout.isatty():
        input("Enter to continue... ")
    else:
      print("Generated README.rst with Pandoc")

  if os.path.isfile('README.rst'):
    with open('README.rst') as fp:
      return fp.read()
  return ''

setup(
  name='docker-remote',
  version='1.0.0',
  license='MIT',
  description='Docker-remote is a wrapper for docker-compose to manage compositions on a remote machine easily.',
  long_description=readme(),
  url='https://github.com/NiklasRosenstein/docker-remote',
  author='Niklas Rosenstein',
  author_email='rosensteinniklas@gmail.com',
  packages=find_packages(),
  entry_points = {
    'console_scripts': [
      'docker-remote = docker_remote.__main__:_entry_point',
      'docker-remote.core.remotepy = docker_remote.core.remotepy:main'
    ]
  }
)
