import logging
from datetime import datetime, timedelta
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import DocType, Date, Index, Keyword, analyzer, Text


class ElasticSearchIndexer():

    class Document(DocType):
        created_at = Date()
        content = Text(fields={'raw': Keyword()},
                       term_vector='with_positions_offsets_payloads')

        def save(self, ** kwargs):
            self.created_at = datetime.now()
            return super().save(** kwargs)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.index_name = None

    def connect(self, host, username, password):
        connections.create_connection(
            hosts=[host], timeout=30, http_auth=('{}:{}'.format(username, password)))
        self.logger.info('Create default connection to ES')

    def create_index(self, index_name):
        index = Index(index_name)
        if index.exists():
            self.logger.info(
                "Index '%s' already exists, skipping creation", index_name)
        else:
            index.settings(number_of_shards=1, number_of_replicas=0)
            index.doc_type(ElasticSearchIndexer.Document)
            index.analyzer(analyzer('html_strip',
                                    tokenizer="standard",
                                    filter=["standard", "lowercase"],
                                    char_filter=["html_strip"]))
            index.create()
        self.index_name = index_name

    def index(self, text):
        doc = ElasticSearchIndexer.Document()
        doc.content = text
        doc.meta.index = self.index_name
        doc.save()
        self.logger.info(
            "Indexed document '%s' with timestamp '%s'", text[0:30], doc.created_at)

    def disconnect(self):
        connections.remove_connection('default')
        self.logger.info('Remove default connection to ES')
