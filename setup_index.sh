#!/bin/bash
set -e
set -x

curl -XDELETE localhost:9200/$1 -s | python -m json.tool

curl -XPUT localhost:9200/$1 -d '
{
  "mappings": {
    "doc": {
      "properties": {
        "id": {"type": "string", "index": "not_analyzed"},
        "path": {"type": "string", "index": "not_analyzed"},
        "suffix": {"type": "string", "index": "not_analyzed"},
        "md5": {"type": "string", "index": "not_analyzed"},
        "sha1": {"type": "string", "index": "not_analyzed"},
        "filetype": {"type": "string", "index": "not_analyzed"},
        "lang": {"type": "string", "index": "not_analyzed"},
        "created-at": {"type": "date", "index": "not_analyzed"},
        "saved-at": {"type": "date", "index": "not_analyzed"}
      }
    }
  }
}
' -s | python -m json.tool
