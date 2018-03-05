## wicked

Wicked is a simple management tool for running `docker-compose` on another
host via `DOCKER_HOST` and an SSH tunnel. It preprocesses your configuration
to ensure any volumes are inside the project directory on the host.

### To do

* Ability to choose a random local port in `wicked.core.tunnel.SSHTunnel`
* Ability to specify a project without requiring a `.wicked-project.toml`
  configuration file, instead via the command-line or/and cached for a
  project directory (which could be saved in a user-global local config file)
* Ability to manage SSH tunnels to docker daemons so that they do not have
  to be re-opened every time the command is called

---

<p align="center">Copyright &copy; 2018 Niklas Rosenstein</p>
