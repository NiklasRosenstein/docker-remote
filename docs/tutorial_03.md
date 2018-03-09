# Tutorial 3: A simple node web app

In this tutorial, we will show the process of creating a simple Node web
application and composing with `docker-remote compose`. Make sure that you
have followed the [Installation instructions](install.md).

Let's start by creating our `package.json` file:

```json
{
  "name": "docker_node_app",
  "version": "1.0.0",
  "description": "Node-App on Docker-Remote",
  "author": "Felix Wohnhaas <felix.wohnhaas@outlook.com>",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.16.2"
  }
}
```

Now we install the express dependency by running:

    $ npm install

Once this basic setup is complete, we are good to go! Let´s create our `server.js` file that will run our node server:

```js
'use strict';

const express = require('express');

const PORT = 4040;
const HOST = '0.0.0.0';

const app = express();

app.get('/', (req, res) => {
    res.send('Hello World from Docker Remote!\n');
});

app.listen(PORT, HOST);
console.log(`Node App running on http://${HOST}:${PORT}`);
```

Next, let us create a Dockerfile that creates an image with Python and the
gunicorn web server:

```Dockerfile
# Dockerfile
FROM node:carbon

# Create app directory
WORKDIR /app

# Copy package(-lock).json
COPY package*.json ./

# Install dependencies
RUN npm install

# Bundle app source
COPY . .

EXPOSE 4040

CMD ["npm", "start"]
```

As we don´t want to copy our local `node_modules` and `npm-debug.log` files, we will add a `.dockerignore` file with the following content:

```.dockerignore
node_modules
npm-debug.log
```

Finally, we add a `docker-compose` configuration:

```yaml
# docker-compose.yml
version: '3'
services:
  web:
    build: .
    ports:
      - "4040:4040"
```

Now we can use the Docker-remote command-line to create a new composition on
the remote machine (or your local machine if you did not configure a different
host). In this example, let's consider that you configured Docker-remote to
operate with your server at `myhost.com`.

```
$ docker-remote -p myapp compose up -d
Created new project 'myapp'
Creating network "myapp_default" with the default driver
Building web
Step 1/7 : FROM node:carbon
 ---> 732a6fe5c376
Step 2/7 : WORKDIR /app
 ---> Using cache
 ---> aa5285b4bc83
Step 3/7 : COPY package*.json ./
 ---> Using cache
 ---> 6d40197d9985
Step 4/7 : RUN npm install
 ---> Using cache
 ---> 86ba4dd1393e
Step 5/7 : COPY . .
 ---> 370beed824a3
Step 6/7 : EXPOSE 4040
 ---> Running in 6555ea673ea5
Removing intermediate container 6555ea673ea5
 ---> 2be47cbbe349
Step 7/7 : CMD ["npm", "start"]
 ---> Running in 380d6dcf9e79
Removing intermediate container 380d6dcf9e79
 ---> c166213e7e08
Successfully built c166213e7e08
Successfully tagged myapp_web:latest
Recreating myapp_web_1 ... done
Attaching to myapp_web_1
web_1  |
web_1  | > docker_node_app@1.0.0 start /app
web_1  | > node server.js
web_1  |
web_1  | Node App running on http://0.0.0.0:4040
```

Now, visit your new Node web application:

    $ curl http://myhost.com:4040
    Hello World from Docker Remote!

Check your applications process information:

```
$ docker-remote -p myapp compose ps
    Name     Command    State           Ports
----------------------------------------------------------------
    myapp   npm start   Up      0.0.0.0:4040->4040/tcp
```

Stop your application and clean up containers:

    $ docker-remote -p myapp compose stop
    $ docker-remote -p myapp compose rm

To avoid having to pass `-p myapp` every time you use Docker Remote, you
can specify the project name in your `docker-compose.yml` configuration.
Note that we set the version to `3.4` as extension fields have been introduced
only with that Compose file format version. While you can use any version
because Docker Remote will strip the field in the preprocessing stage, the
file would be invalid for use with plain `docker-compose`.

```yaml
# docker-compose.yml
version: '3.4'
services:
  web:
    build: .
    ports:
      - "8000:8000"
x-docker-remote:
  project:
    name: myapp
```

Now you can skip specifying the project-name on the command-line.

    $ docker-remote compose up --build --detach
