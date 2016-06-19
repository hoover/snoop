from django.conf import settings
from elasticsearch import Elasticsearch, helpers
es = Elasticsearch(settings.ELASTICSEARCH_URL)
query = {"filter": {"wildcard": {"text": "*"}}, "_source": false}
with open('../rel1.txt', 'w', encoding='utf-8') as f:
    for doc in helpers.scan(es, index='hoover-6', query=query, size=10000):
        print(doc['_id'], file=f)

# should return 1231116 documents
