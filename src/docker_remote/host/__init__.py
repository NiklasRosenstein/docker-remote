# empty

from . import dockerhost
from . import projects


def get_version():
    from docker_remote import __version__
    return __version__
