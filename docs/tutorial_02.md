## Tutorial 2: Web scraper

Docker-remote is also usefult to run one-off applications. If the data that
they produce is stored on mapped volumes, these volumes can then be downloaded
conveniently with Docker-remote.

Let's start by creating a very simple web scraper that stores every URL it
can find in a Postgres Database.

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

def init_tables():
  cur = con.cursor()
  cur.execute('''CREATE TABLE IF NOT EXISTS links (
    url TEXT PRIMARY KEY
  )''')

def main():
  init_database()
  global con
  with psycopg2.connect(database='links', user='postgres',
      host='database', password='password') as con:
    init_tables()

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

if __name__ == '__main__':
  main()
```

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
