## wicked

Wicked is a wrapper for `docker-compose` that allows you to manage Docker
compositions on a remote machine easily. It automatically opens an SSH tunnel
for the docker daemon and wraps the `docker` and `docker-compose` commands.

__Host Requirements__

* Docker-CE (not tested with Docker-EE)
* A `root` user with your SSH public key in `/root/.ssh/authorized_keys`
* A system user called `wicked` with the Wicked command-line tools installed

__Client Requirements__

* An SSH private key installed on the host's `root` account
* Optionally, an SSH private key installed on the host's `wicked` account
* The Wicked command-line tools

### Set-up

On the host machine, create a user called `wicked` and install this package.
Also add your SSH public key to the authorized_keys of the `root` and
optionally the `wicked` user. If you do not add your public key to the latter,
you will need to specify the password in your client configuration.

    $ sudo nano /root/.ssh/authorized_keys
    $ sudo useradd wicked -m --shell /bin/bash -p wicked
    $ sudo su wicked && cd
    $ pip3 install --user git+https://github.com/NiklasRosenstein/wicked.git
    $ wicked --version  # Ensure that you can use the command-line tools
    Wicked 1.0.0
    $ nano ~/.ssh/authorized_keys

On the client, install the Wicked command-line tools.

    $ pip3 install --user git+https://github.com/NiklasRosenstein/wicked.git
    $ wicked --version
    Wicked 1.0.0
    $ cat ~/.wicked.toml
    [remote]
    host = "myhost.com"  # The name of the host that you installed Wicked on
    user = "wicked"  # Default
    password = "..."  # The password if you did not add your public key
    $ nano docker-compose.yml
    $ wicked -p my_project compose up -d  # Compose a container on the remote
    $ wicked -p my_project scp data  # Download the volume directories to "./data"

### Configuration

You can place the wicked configuration in `~/.wicked.toml` and `./wicked.toml`.
The local configuration should be used only for a project if you want to use a
different remote configuration or fix the project name.

#### [project] name

The project name. Should only be specified in the local directories'
`wicked.toml` configuration file. If no project name is explicitly specified
on the command-line, this value is used.

#### [host] project_root

This is used only on the Wicked host machine. Defaults to the home directory
of the user through which the Wicked command-line is called (which is usually
the `wicked` user). This is the directory where project directories will be
located. Currently project directories are only used for volumes.

#### [remote] host

The host name of the remote machine. Defaults to `localhost`. In the case of
`localhost`, your machine does not need an SSH server installed.

#### [remote] user

The user name. Not used if `[remote] host` is `localhost`. Defaults to
`wicked`. Note that this is independent from the SSH tunnel username option,
which defaults to `root`.

#### [remote] password

The password of the user on the `[remote] host`.

#### [tunnel] remote_user

The username of the remote through which an SSH tunnel to the Docker daemon
should be created. This user is also used for the `wicked scp` command for
downloading project data. Defaults to `root`.

#### [tunnel] local_port

The local port to bind the SSH tunnel to. Defaults to `2375`.

#### [tunnel] remote_port

The remote port to bind the SSH tunnel to. Defaults to the
`/var/run/docker.sock` socket file.

---

<p align="center">Copyright &copy; 2018 Niklas Rosenstein</p>
