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

## Setting things up

1. Configuration - create `snoop/site/settings/local.py` with:

   * `DATABASES`: django database configuration
   * `SNOOP_ROOT`: path to the dump
   * `ELASTICSEARCH_URL`: url to elasticsearch server
   * `ELASTICSEARCH_INDEX`: name of elasticsearch index where to index the data

   Recommended: set up the dependencies below.

2. Create file and folder entries in the database:

   ```shell
   $ ./manage.py walk
   ```

3. Select documents for analysis. The argument to the `digestqueue` command is
   an SQL `WHERE` clause to choose which documents will be analyzed. `true`
   means all documents. They are added to the `digest` queue.

   ```shell
   $ ./manage.py digestqueue "true"
   ```

4. Run the `digest` worker to process. All documents successfully digested will
   be automatically added to the `index` queue.

   ```shell
   $ ./manage.py worker digest
   ```

5. Create/reset the elasticsearch index that you set up as `ELASTICSEARCH_INDEX`.

   ```shell
   $ ./manage.py resetindex
   ```

6. Run the `index` worker to push digested documents to elasticsearch.

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
   * `TIKA_SERVER_ENDPOINT`: url to tika server.
      For a local server running with default settings,
      this should be `http://localhost:9998/`
   * `MAX_TIKA_FILE_SIZE`: in bytes. Files larger than this won't be sent to tika.
   * `TIKA_FILE_TYPES`: a list of categories of files to send to tika.
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

Configure `SEVENZIP_BINARY` to the `7z` binary's path.
If it's installed system-wide, just use `7z`.

Set `ARCHIVE_CACHE_ROOT` to an existing folder with write access.
This folder will serve as a cache for all the extracted archives.

### `msgconvert` (for Outlook `.msg` emails)

Current setup uses the `msgconvert` script to convert `.msg` emails to `.eml`.
Docs: http://www.matijs.net/software/msgconv/

```shell
$ cpan -i Email::Outlook::Message
```

Set `MSGCONVERT_SCRIPT` to the script's path.
If it's installed system-wide, just use `msgconvert`.


### `readpst` (for Outlook `.pst` and `.ost` emails)

Current setup uses the `readpst` binary to convert `.pst` and `.ost` emails to
the mbox format.

```shell
$ brew install libpst  #  mac
$ apt-get install libpst pst-utils  #  debian / ubuntu
```

Set `READPST_BINARY` to the binary's path.
If it's installed system-wide, just use `readpst`.

Set `SNOOP_PST_CACHE_ROOT` to an existing folder with write access.


### `gpg` for Hushmail-like emails

Set:
   * `SNOOP_GPG_HOME`: path to the existing gpg home directory with keys to be used for decryption
   * `SNOOP_GPG_BINARY`: path to the `gpg` binary to be used in conjuction with `SNOOP_GPG_HOME`

