<a href="https://opensource.org/licenses/MIT">
  <img align="right" src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</a>

# docker-remote

<img src="docs/logo.png" alt="docker-remote Logo">

  [Compose]: https://github.com/docker/compose
  [Machine]: https://docs.docker.com/machine/

Docker-remote is a command-line tool for deploying Docker containers on a
remote host via SSH.

__Features__

* Allows you to compose and manage applications remotely
* Pre-processes your Docker Compose configuration in order to place all
  named and relative volume names inside the project directory.
* Built-in support for adding `dockerhost` hostname to `/etc/hosts` for
  all or selected services

## Installation & Configuration

Get the newest stable release from Pip:

    $ pip install docker-remote

Configure the details for the host that you are going to connect to (this can
also be configured on a project level):

    # ~/.docker-remote.yml
    remote:
      host: example.org
      user: docker-user

> **Note**: At this point, you will need SSH to be set up in a way that allows
> the `ssh` command to connect to and login as `docker-user@example.org`
> without prompting for a password.

Install docker-remote on the host:

    $ docker-remote install

Start your first project:

    $ cat docker-compose.yml
    version: '3.4'
    services:
      web:
        image: nginx
        ports:
          - "0.0.0.0:80:80"
    x-docker-remote:
      project:
        name: nginx-test
    $ docker-remote compose up -d
    $ docker-remote list
    nginx-test


Check out the [Documentation](docs/) for more examples.

---

<p align="center">Copyright &copy; 2019 Niklas Rosenstein</p>
