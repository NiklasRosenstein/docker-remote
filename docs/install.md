## Docker Remote Installation

Docker Remote requires access to the `root` user on the remote machine in
order to gain the proper privileges to communicate with the Docker Daemon.
Internally, Docker Remote uses the `ssh` command for all connections. It is
highly recommended to create a private/public keypair and place your private
key pair in the root's `authorized_keys` file. If your keypair is encrypted
with a password, we also recommend using `ssh-agent`.

### Client Installation

Install the Docker Remote client via Pip

    pip3 install git+https://github.com/NiklasRosenstein/docker-remote.git
    docker-remote --version

### Host Installation

After installing Docker Remote on your client machine, you can easily install
and upgrade Docker Remote on a host by using the `docker-remote install` command.
This will run a Bash script that installs Docker Remote via Pip and ensure that
the `$HOME/.local/bin` directory is in your `PATH`.

    docker-remote -H myhost.com install --via pip3.6 --ref master

Note that you can skip the `-H myhost.com` if you configured the host in
the `~/.docker-remote.yml` configuration file.

```yaml
remote:
  host: myhost.com
```
