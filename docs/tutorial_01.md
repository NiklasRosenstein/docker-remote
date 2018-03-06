# Tutorial 1: A simple web app

In this tutorial, we will show the process of creating a simple Python web
application and composing with `docker-remote compose`. Make sure that you
have followed the [Installation instructions](install.md).

Let's start by creating our Python program:

```python
# app.py
import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
  return "Hello, world!"
```

Now let us create a Dockerfile that creates an image with Python and the
gunicorn web server:

```Dockerfile
# Dockerfile
FROM python:latest
RUN pip install flask gunicorn
WORKDIR /app
COPY . .
ENTRYPOINT gunicorn app:app -b 0.0.0.0:8000
```

And then we add a Docker-compose configuration:

```yaml
# docker-compose.yml
version: '3'
services:
  web:
    build: .
    ports:
      - "8000:8000"
```

Now we can use the Docker-remote command-line to create a new composition on
the remote machine (or your local machine if you did not configure a different
host). In this example, let's consider that you configured Docker-remote to
operate with your server at `myhost.com`.

```
$ docker-remote compose up -d
Created new project 'full_case'
Creating network "fullcase_default" with the default driver
Building web
Step 1/5 : FROM python:latest
 ---> 336d482502ab
Step 2/5 : RUN pip install flask gunicorn
 ---> Using cache
 ---> 303cb95d3eb1
Step 3/5 : WORKDIR /app
 ---> Using cache
 ---> 2487b35b4551
Step 4/5 : COPY . .
 ---> 992b085e9ecd
Step 5/5 : ENTRYPOINT gunicorn app:app -b 0.0.0.0:8000
 ---> Running in 29de64ba77e6
Removing intermediate container 29de64ba77e6
 ---> db9ddb52ac7a
Successfully built db9ddb52ac7a
Successfully tagged fullcase_web:latest
WARNING: Image for service web was built because it did not already exist. To rebuild this image you must use `docker-compose build` or `docker-compose up --build`.
Creating fullcase_web_1 ... done
```

You can see that Docker-remote has allocated a random project name. If we were
using volumes in the Docker-compose configuration, these volumes would be
placed in the project directory.

Now, visit your new Python web application:

    $ curl http://myhost.com:8000
    Hello, world!

Check your applications process information:

```
$ docker-remote -p full_case compose ps
     Name                   Command               State           Ports
--------------------------------------------------------------------------------
fullcase_web_1   /bin/sh -c gunicorn app:ap ...   Up      0.0.0.0:8000->8000/tcp
```

Stop your application and clean up containers:

```
$ docker-remote -p full_case compose stop
$ docker-remote -p full_case compose rm
```
