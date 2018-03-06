## Installing Docker-remote

### Requirements

__Host Requirements__

* Docker-CE (not tested with Docker-EE)
* A `root` user with your SSH public key in `/root/.ssh/authorized_keys`
* A system user called `docker-remote` with the docker-remote command-line
  tools installed, optionally with your SSH public key installed in
  `/home/docker-remote/.ssh/authorized_keys`

__Client Requirements__

* An SSH private key installed on the host's `root` account
* The docker-remote command-line tools

> Note: You can also use Docker-remote on just the localhost. In this case,
> the only advantage it provides is the preprocessing of the docker-compose
> configuration file, placing volumes in a project directory.
>
> By default, Docker-remote is configured to work on the localhost. Note
> that it will not use SSH when `[remote] host` is `localhost`.

### Set-up

On the host machine, create a user called `docker-remote` and install this package.
Also add your SSH public key to the authorized_keys of the `root` and
optionally the `docker-remote` user. If you do not add your public key to the latter,
you will need to specify the password in your client configuration.

    $ sudo nano /root/.ssh/authorized_keys
    $ sudo useradd docker-remote -m --shell /bin/bash -p docker-remote
    $ sudo su docker-remote && cd
    $ pip3 install --user git+https://github.com/NiklasRosenstein/docker-remote.git
    $ docker-remote --version  # Ensure that you can use the command-line tools
    Docker-remote 1.0.0
    $ nano ~/.ssh/authorized_keys

On the client, install the docker-remote command-line tools.

    $ pip3 install --user git+https://github.com/NiklasRosenstein/docker-remote.git
    $ docker-remote --version
    Docker-remote 1.0.0
    $ cat ~/.docker-remote.toml
    [remote]
    host = "myhost.com"  # The name of the host that you installed docker-remote on
    user = "docker-remote"  # Default
    password = "..."  # The password if you did not add your public key
    $ nano docker-compose.yml
    $ docker-remote -p my_project compose up -d  # Compose a container on the remote
    $ docker-remote -p my_project scp data  # Download the volume directories to "./data"
