## Docker-remote command-line interface

```
usage: docker-remote [-h] [--version] [-p PROJECT_NAME] [-H HOST] [-v]
                     {tunnel,shell,ls,rm,scp,docker,compose} ...

positional arguments:
  {tunnel,shell,ls,rm,scp,docker,compose}
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
    compose             Wrapper for docker compose.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -p PROJECT_NAME, --project-name PROJECT_NAME
                        The project name. If this option is omitted, it will
                        be read from the configuration file or fall back on a
                        random project name.
  -H HOST, --host HOST  The name of the Docker host. If this option is
                        omitted, it will be read from the configuration file
                        or fall back on "localhost". In the case of
                        "localhost", no SSH tunnel will be created. This
                        option may include the user in the form of
                        "user@host".
  -v, --verbose         Generate more output, such as sub-commands that are
                        being invoked.
```
