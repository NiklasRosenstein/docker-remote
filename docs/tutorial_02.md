## Tutorial 2: Web scraper

Docker-remote is also usefult to run one-off applications. If the data that
they produce is stored on mapped volumes, these volumes can then be downloaded
conveniently with Docker-remote.

Let's start by creating a very simple web scraper that stores every URL it
can find in a Postgres Database.

<script src="https://gist.github.com/NiklasRosenstein/64f268d4129228d8c9f3e2ae64d9366c.js"></script>

Now lets us create a Docker-compose configuration with two containers: One
for the Python script and the other for the Postgres database.

```yaml
# docker-compose.yml
version: '3'
services:
  scraper:
    build: .
    links:
      - "db:database"
  db:
    image: "postgres"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    expose:
      - "5432"
    volumes:
      - data:/var/lib/postgresql/data
```

And a Dockerfile that installs all the dependencies for our scraper:

```Dockerfile
FROM python:latest
RUN pip install bs4 html5lib requests psycopg2
WORKDIR /app
COPY . .
ENTRYPOINT python scraper.py
```

Now we can run this composition with Docker-remote. Note that the `data`
volume of the `db` service will be automatically mapped to a directory
in the project directory that is automatically created for your composition.

```
$ docker-remote -p webscraper compose up -d
$ docker-remote -p webscraper compose logs scraper -f
Attaching to myapp_scraper_1
scraper_1  | https://google.com
scraper_1  | https://www.google.de/imghp?hl=de&tab=wi
scraper_1  | https://maps.google.de/maps?hl=de&tab=wl
scraper_1  | https://play.google.com/?hl=de&tab=w8
scraper_1  | https://www.youtube.com/?gl=DE&tab=w1
scraper_1  | https://news.google.de/nwshp?hl=de&tab=wn
scraper_1  | https://mail.google.com/mail/?tab=wm
scraper_1  | https://drive.google.com/?tab=wo
scraper_1  | https://www.google.de/intl/de/options/
...
```

To retrieve the data, we can simply enter the database service and dump the
database.

```
$ docker-remote -p myapp compose exec db psql -U postgres -d links -c "COPY links TO stdout DELIMITER ',' CSV HEADER"
url
https://google.com
https://www.google.de/imghp?hl=de&tab=wi
https://maps.google.de/maps?hl=de&tab=wl
https://play.google.com/?hl=de&tab=w8
https://www.youtube.com/?gl=DE&tab=w1
https://news.google.de/nwshp?hl=de&tab=wn
https://mail.google.com/mail/?tab=wm
https://drive.google.com/?tab=wo
https://www.google.de/intl/de/options/
...
```

Note that the database service must be running for this command to work. If
you already stopped the containers, spin up the database service again using
this command:

    $ docker-remote -p myapp compose start db
