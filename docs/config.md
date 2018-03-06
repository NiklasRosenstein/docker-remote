## Configuration

You can place the docker-remote configuration in `~/.docker-remote.toml` and
`./docker-remote.toml`. The local configuration should be used only for a
project if you want to use a different remote configuration or fix the project
name. Example:

```toml
[project]
name = "myapp"
```

Additionally, you can specify additional configuration values in the
`x-docker-remote` field of the `docker-compose.yml` configuration. Example:

```yaml
version: '3'
services:
  web:
    build: .
x-docker-remote:
  project:
    name: myapp
```

#### [project] name

The project name. Should only be specified in the local directories'
`docker-remote.toml` configuration file. If no project name is explicitly specified
on the command-line, this value is used.

#### [host] project_root

This is used only on the docker-remote host machine. Defaults to the home directory
of the user through which the docker-remote command-line is called (which is usually
the `docker-remote` user). This is the directory where project directories will be
located. Currently project directories are only used for volumes.

#### [remote] host

The host name of the remote machine. Defaults to `localhost`. In the case of
`localhost`, your machine does not need an SSH server installed.

#### [remote] user

The user name. Not used if `[remote] host` is `localhost`. Defaults to
`docker-remote`. Note that this is independent from the SSH tunnel username option,
which defaults to `root`.

#### [remote] password

The password of the user on the `[remote] host`.

#### [tunnel] remote_user

The username of the remote through which an SSH tunnel to the Docker daemon
should be created. This user is also used for the `docker-remote scp` command for
downloading project data. Defaults to `root`.

#### [tunnel] local_port

The local port to bind the SSH tunnel to. Defaults to `2375`.

#### [tunnel] remote_port

The remote port to bind the SSH tunnel to. Defaults to the
`/var/run/docker.sock` socket file.
