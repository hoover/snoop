# Snoop

Snoop will walk a file dump, extract text and metadata for each
document found and index that data into elasticsearch.

Snoop serves as a standalone web server that outputs all the data
available for each indexed document.


## Supported file formats

   * Documents: rtf, doc, xls, ppt & variants
   * Emails: eml, emlx, msg
   * Archives: zip, rar, 7z, tar
   * Text files
   * Html pages

## Installation
Snoop depends on _lxml_ (which compiles against _libxml2_ and _libxslt_) and
_psycopg2_ (which compiles against the PostgreSQL client headers). On
Debian/Ubuntu the required packages are `build-essential`, `python3-dev`,
`libxml2-dev`, `libxslt1-dev` and `postgresql-server-dev-9.4` (or newer).

Snoop can talk to a bunch of tools. Some understand a certain data format,
others do useful processing. See "Optional Dependencies" to install them.

1. Create a virtualenv and run `pip install -r requirements.txt`

2. Configuration - create `snoop/site/settings/local.py`, you can use
   `example_local.py` as a template.

   * `DATABASES`: django database configuration
   * `SNOOP_ROOT`: path to the dump
   * `SNOOP_ELASTICSEARCH_URL`: url to elasticsearch server
   * `SNOOP_ELASTICSEARCH_INDEX`: name of elasticsearch index where to index
     the data
   * `SNOOP_LOG_DIR`: path to the dir where worker logs will be dumped

3. Run the migrations:

   ```shell
   $ ./manage.py migrate
   ```

## Getting started

1. List the files in the dump, from the path configured in `SNOOP_ROOT`, and
   create entries in the database.

   ```shell
   $ ./manage.py walk
   ```

2. Select documents for analysis. The argument to the `digestqueue` command is
   an SQL `WHERE` clause to choose which documents will be analyzed. `true`
   means all documents. They are added to the `digest` queue.

   ```shell
   $ ./manage.py digestqueue
   ```

3. Run the `digest` worker to process. All documents successfully digested will
   be automatically added to the `index` queue. Run as many of these processes
   as you want, they don't spawn any threads but are designed to be concurrent.

   ```shell
   $ ./manage.py worker digest
   ```

   The `worker` command accepts a `-x`

4. Create/reset the elasticsearch index that you set up as `ELASTICSEARCH_INDEX`.

   ```shell
   $ ./manage.py resetindex
   ```

5. Run the `index` worker to push digested documents to elasticsearch.

   ```shell
   $ ./manage.py worker index
   ```

To digest a single document and view the JSON output:

```shell
$ ./manage.py digest 123
```

## Optional Dependencies


### Apache Tika (for metadata extraction)

Tika is used for text, language and metadata extraction.

You can download the server .jar and run it with:

```shell
$ java -jar tika-server-1.13.jar
```

After that, configure the following settings:
   * `SNOOP_TIKA_SERVER_ENDPOINT`: url to tika server.
      For a local server running with default settings,
      this should be `http://localhost:9998/`
   * `SNOOP_TIKA_MAX_FILE_SIZE`: in bytes. Files larger than this won't be sent to tika.
   * `SNOOP_TIKA_FILE_TYPES`: a list of categories of files to send to tika.
      Possible values are: `['pdf', 'doc', 'ppt', 'text', 'xls']`.
   * `SNOOP_ANALYZE_LANG`: `True` to use Tika for language detection for
      documents that have text.

### `7z` (for archive extraction)

Current setup uses `7z` to process archives.
On Debian/linux, use the `p7zip` implementation.
Rar support is also needed.

```shell
$ sudo apt-get install p7zip-full
$ sudo apt-get install p7zip-rar
```

Configure `SNOOP_SEVENZIP_BINARY` to the `7z` binary's path.
If it's installed system-wide, just use `7z`.

Set `SNOOP_ARCHIVE_CACHE_ROOT` to an existing folder with write access.
This folder will serve as a cache for all the extracted archives.

### `msgconvert` (for Outlook `.msg` emails)

Current setup uses the `msgconvert` script to convert `.msg` emails to `.eml`.
Docs: http://www.matijs.net/software/msgconv/

```shell
$ cpan -i Email::Outlook::Message
```

Set `SNOOP_MSGCONVERT_SCRIPT` to the script's path.
If it's installed system-wide, just use `msgconvert`.

Set `SNOOP_MSG_CACHE` to an existing folder with write access.


### `readpst` (for Outlook `.pst` and `.ost` emails)

Current setup uses the `readpst` binary to convert `.pst` and `.ost` emails to
the mbox format.

```shell
$ brew install libpst  #  mac
$ sudo apt-get install pst-utils  #  debian / ubuntu
```

Set `SNOOP_READPST_BINARY` to the binary's path.
If it's installed system-wide, just use `readpst`.

Set `SNOOP_PST_CACHE_ROOT` to an existing folder with write access.


### `gpg` for Hushmail-like emails

Set:
   * `SNOOP_GPG_HOME`: path to the existing gpg home directory with keys to be used for decryption
   * `SNOOP_GPG_BINARY`: path to the `gpg` binary to be used in conjuction with `SNOOP_GPG_HOME`
