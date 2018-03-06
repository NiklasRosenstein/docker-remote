## docker-remote (WIP)

Docker-remote is a wrapper for `docker-compose` that allows you to manage Docker
compositions on a remote machine easily. It automatically opens an SSH tunnel
for the docker daemon and wraps the `docker` and `docker-compose` commands.

By wrapping `docker-compose`, docker-remote can update your configuration file
to ensure that relative volume paths are converted to absolute paths inside a
project directory on the host.

Check out the [Documentation](docs/) for installation instructions and
tutorials.

---

<p align="center">Copyright &copy; 2018 Niklas Rosenstein</p>
