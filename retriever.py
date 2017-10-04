import logging
from indexer import ElasticSearchIndexer
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.query import Range, Term
from elasticsearch.exceptions import NotFoundError


class Retriever:
    def __init__(self, index_name):
        self.logger = logging.getLogger(__name__)
        self.index_name = index_name

    def connect(self, host, username, password):
        connections.create_connection(
            hosts=[host], timeout=20, http_auth=('{}:{}'.format(username, password)))
        self.logger.info('Create default connection to ES')

    def disconnect(self):
        connections.remove_connection('default')
        self.logger.info('Remove default connection to ES')

    def _response_to_dict(self, response):
        result = {'hits': 0}
        for hit in response:
            result['hits'] = response.hits.total
            result['docs'] = result.get(
                'docs', []) + [{'id': hit.meta.id, 'created_at': hit.created_at, 'content': hit.content}]
        return result

    def docs_by_range(self, from_date, to_date, limit=10):
        query = Range(created_at={'gte': from_date, 'lt': to_date})
        return self._response_to_dict(Search().query(query)[0:limit].execute())

    def docs_by_term(self, term, limit=10):
        query = Term(content=term)
        return self._response_to_dict(Search().query(query)[0:limit].execute())

    def doc_by_id(self, id):
        try:
            response = ElasticSearchIndexer.Document.get(
                id=id, index=self.index_name)
            result = response.to_dict()
            result['id'] = response.meta.id
            return result
        except NotFoundError:
            return {}

    def docs_by_id(self, ids):
        result = []
        response = ElasticSearchIndexer.Document.mget(
            docs=ids, index=self.index_name)
        for doc in response:
            if doc is not None:
                res = doc.to_dict()
                res['id'] = doc.meta.id
                result.append(res)
            else:
                result.append({})
        return result

    def term_stats(self, ids, term):
        conn = connections.get_connection()
        result = {term: {'freq': 0, 'doc_freq': 0, 'total_freq': 0}}

        for id in ids:
            termvector = conn.termvectors(index=self.index_name, doc_type='document', id=id,
                                          field_statistics=True, fields=['content'], term_statistics=True)
            if termvector['found']:

                for t, v in termvector['term_vectors']['content']['terms'].items():
                    if t == term:
                        result[t]['freq'] = result[t]['freq'] + \
                            int(v['term_freq'])
                        result[t]['doc_freq'] = int(v['doc_freq'])
                        result[t]['total_freq'] = int(v['ttf'])

        return result
