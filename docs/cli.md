## Docker-remote command-line interface

```
usage: docker-remote [-h] [--version] [-p PROJECT_NAME] [-H HOST] [-v]
                     {tunnel,shell,ls,rm,scp,docker,compose,install} ...

positional arguments:
  {tunnel,shell,ls,rm,scp,docker,compose,install}
    tunnel              Create a tunnel to a docker daemon.
    shell               Create a tunnel and enter a new shell. Inside this
                        shell, a docker-compose alias is created to route
                        through docker-remote, allowing you to use your normal
                        docker-compose workflow while having the benefits of
                        docker-remote.
    ls                  List projects on the host.
    rm                  Delete a project on the host.
    scp                 Download a volume or multiple volume directories from
                        the host. If no volumes are specified, the whole
                        project directory is downloaded.
    docker              Wrapper for docker.
    compose             Wrapper for docker-compose.
    install             Install docker-remote on a host. This will run a bash
                        script on the root user of the host specified with the
                        -H option or the `[remote] host` configuration to
                        install the latest version of docker-remote via Pip (a
                        user install). The script will also ensure that the
                        docker-remote command-line can be found by adding
                        $HOME/.local/bin to the PATH in .bashrc.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -p PROJECT_NAME, --project-name PROJECT_NAME
                        The project name. If this option is omitted, it will
                        be read from the configuration file.
  -H HOST, --host HOST  The name of the Docker host. If this option is
                        omitted, it will be read from the configuration file
                        or fall back on "localhost". In the case of
                        "localhost", no SSH tunnel will be created. This
                        option may include the user in the form of
                        "user@host".
  -v, --verbose         Generate more output, such as sub-commands that are
                        being invoked.
```
