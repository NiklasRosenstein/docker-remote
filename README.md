## wicked

Wicked is a simple management tool for running `docker-compose` on another
host via `DOCKER_HOST` and an SSH tunnel. It preprocesses your configuration
to ensure any volumes are inside the project directory on the host.

### To do

* Ability to choose a random local port in `wicked.core.tunnel.SSHTunnel`
* `wicked compose` command as a wrapper for `docker-compose` that creates
  a tunnel to the remote docker daemon and preprocesses the relative volume
  paths in the configuration

---

<p align="center">Copyright &copy; 2018 Niklas Rosenstein</p>
