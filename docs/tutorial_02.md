## Tutorial 2: Web scraper

Docker-remote is also usefult to run one-off applications. If the data that
they produce is stored on mapped volumes, these volumes can then be downloaded
conveniently with Docker-remote.

### Using the Docker Remote Shell

Let's start by using the Docker Remote Shell feature which will allow us to
use the standard Docker Compose workflow without having to use the
`docker-remote` command-line explicitly with each command.

    $ docker-remote shell
    Setting up docker-compose alias...
    $ alias
    alias docker-compose='docker-remote compose'

If you now use `docker` or `docker-compose`, it will be the same as if you
used `docker-remote docker` or `docker-remote compose`.

    $ docker ps
    # This should list all containers on your remote Docker host.

### A simple Python web scraper

The following is a very basic web scraper that uses a PostgresSQL database
driver to save any link it finds to a database, starting from Google.

```python
# scraper.py
import collections
import bs4
import requests
import psycopg2, psycopg2.extensions
import sys
import urllib.parse

con = None
queue = collections.deque()

def init_database():
  with psycopg2.connect(database='postgres', user='postgres',
      host='database', password='password') as con:
    con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'links'")
    if not cur.fetchone():
      print('Creating database ...')
      cur.execute("CREATE DATABASE links")

def init_tables(con):
  cur = con.cursor()
  cur.execute('''CREATE TABLE IF NOT EXISTS links (
    url TEXT PRIMARY KEY
  )''')

def scrape(con):
  cur = con.cursor()
  queue.append('https://google.com')
  while queue:
    url = queue.popleft()
    cur.execute("SELECT 1 FROM links WHERE url=%s", (url,))
    if cur.fetchone():
      continue  # already exists
    print(url)
    sys.stdout.flush()
    cur.execute("INSERT INTO links (url) VALUES (%s) ON CONFLICT (url) DO NOTHING", (url,))
    con.commit()
    try:
      text = requests.get(url).text
    except requests.RequestException as exc:
      print('[{}] -- {}'.format(url, exc))
    else:
      for anchor in bs4.BeautifulSoup(text, 'html5lib').find_all('a'):
        try:
          info = urllib.parse.urlparse(anchor['href'])
        except KeyError:
          continue
        if (not info.scheme and not info.netloc and info.path) or \
            (info.scheme in ('http', 'https') and info.netloc):
          queue.append(urllib.parse.urljoin(url, anchor['href']))
  print('Done.')

def main():
  init_database()
  with psycopg2.connect(database='links', user='postgres',
      host='database', password='password') as con:
    init_tables(con)
    scrape(con)

if __name__ == '__main__':
  main()
```

### Compositing the application

Now lets us create a Docker Compose configuration with two containers: One
for the Python script and the other for the Postgres database. Also let us
specify the project name so we can omit it in the `docker-compose`
command-line.

```yaml
# docker-compose.yml
version: '3.4'
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
x-docker-remote:
  project:
    name: webscraper
```

And a Dockerfile that installs all the dependencies for our scraper:

```Dockerfile
FROM python:latest
RUN pip install bs4 html5lib requests psycopg2
WORKDIR /app
COPY . .
ENTRYPOINT python scraper.py
```

Now we can run this composition with Docker Compose. Since we are inside the
Docker Remote Shell, what this will actually do is first go through the Docker
Remote wrapper for the preprocessing steps.

Note that the `data` volume of the `db` service will be automatically mapped
to a directory in the project directory that is automatically created for your
composition. If your project directory on your host is `/home/docker-remote/`
then the database volume will be mounted at `/home/docker-remote/webscraper/data`.

```
$ docker-compose up -d
$ docker-compose logs scraper -f
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

> **To do**: You may notice a connection error of the Python script to the
> Postgres database when you first start the containers. This is because
> the Postgres container needs some time to initialize the data directory
> and at the time the Python container attempts to connect, it is not yet
> running.
>
> Is there a solution or best practice to overcome this issue?

To retrieve the data, we can simply enter the database service and dump the
database.

```
$ docker-compose exec db psql -U postgres -d links -c "COPY links TO stdout DELIMITER ',' CSV HEADER"
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

    $ docker-compose start db
