## Extract text from file dump

1. Configuration - create a file `maldini/site/settings/local.py`:

   * `DATABASES`: django database configuration
   * `MALDINI_ROOT`: path to the dump
   * `ELASTICSEARCH_URL`: url to elasticsearch server
   * `ELASTICSEARCH_INDEX`: name of elasticsearch index where to index the data

2. Create file and folder entries in the database:

   ```shell
   $ ./manage.py walk
   $ ./manage.py walkfolders
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
   $ ./manage.py digestworker
   ```

5. Run the `index` worker to push digested documents to elasticsearch.

   ```shell
   $ ./manage.py indexworker
   ```

To digest a single document and view the JSON output:

```shell
$ ./manage.py digest 123
```
