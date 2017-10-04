"""
IndexService

 Usage:
   index_service.py ingester <password> <config> [-v]
   index_service.py server <config> [-v]
   index_service.py -h | --help
   index_service.py --version

 Options:
  -v  Verbose Mode
"""

import atexit
import logging
from configparser import ConfigParser
import endpoint
from docopt import docopt
from ingester import Ingester
from indexer import ElasticSearchIndexer
from requests.exceptions import ConnectionError as RequestsConnectionError
from retriever import Retriever
import requests
import time

logger = logging.getLogger(__name__)


def prepare_ingester(config):
    ingester_password = config.get('Ingester', 'Password')
    source = config.get('Ingester', 'Source')
    webhook = config.get('Ingester', 'Webhook')
    keywords = config.get('Ingester', 'Keywords').split(',')
    keywords = list(map(str.strip, keywords))

    host = config.get('ElasticSearch', 'Host')
    username = config.get('ElasticSearch', 'Username')
    password = config.get('ElasticSearch', 'Password')
    indexname = config.get('ElasticSearch', 'Indexname')

    ingester = Ingester(source, ingester_password)
    indexer = ElasticSearchIndexer()
    indexer.connect(host, username, password)
    atexit.register(indexer.disconnect)
    indexer.create_index(indexname)

    return ingester, indexer, keywords, webhook


def _send_alert(url, term, times):
    call = url + term + '/' + str(times)
    r = requests.get(call)
    if r.status_code != 200:
        logger.warn("Could not generate alert to '%s'. Error code %s",
                    call, r.status_code)
    else:
        logger.info("Observed word '%s'. Generate alert '%s'",
                    term, call)


def _check_contains(term, text):
    return text.lower().count(' ' + term.lower() + ' ')


def _alert(url, keywords, text):
    for kw in keywords:
        count = _check_contains(kw, text)
        if count > 0:
            _send_alert(url, kw, count)


def ingest(ingester, indexer, keywords, webhook):
    try:
        for status, text in ingester.ingest():
            if status != 200:
                logger.warn("Can't connect to %s. Status code %s",
                            ingester.get_source(), status)
                return
            else:
                if len(text) > 20:
                    try:
                        indexer.index(text)
                        _alert(webhook, keywords, text)
                    except Exception as e:
                        logger.warn("Catch exception '%s'", str(e)[0:50])
                        logger.warn("Skipping document '%s'", text[0:50])
    except RequestsConnectionError:
        logger.warn("Can't connect to %s", ingester.get_source())


def run_ingester(config):
    ingester, indexer, keywords, webhook = prepare_ingester(config)
    retries = config.getint('Ingester', 'Retries')
    sleep = config.getint('Ingester', 'Sleep')
    for i in range(1, retries + 1):
        logger.info('Running ingester %s times of %s', i, retries)
        ingest(ingester, indexer, keywords, webhook)
        if i < retries:
            logger.info('Sleeping for %s seconds', sleep)
            time.sleep(sleep)


def prepare_server(config):
    host = config.get('ElasticSearch', 'Host')
    username = config.get('ElasticSearch', 'Username')
    password = config.get('ElasticSearch', 'Password')
    indexname = config.get('ElasticSearch', 'Indexname')

    retriever = Retriever(index_name=indexname)
    retriever.connect(host, username, password)
    atexit.register(retriever.disconnect)
    return retriever


def run_server(config):
    logger.info("Running server")
    endpoint.retriever = prepare_server(config)
    endpoint.app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    LOG_LEVELS = {0: logging.INFO, 1: logging.DEBUG}
    CONFIG_KEY = 'IndexService'
    arguments = docopt(__doc__, version='IndexService 1.0')
    logger.setLevel(level=LOG_LEVELS[arguments.get('-v')])
    logging.basicConfig(level=LOG_LEVELS[arguments.get('-v')])
    logging.getLogger('elasticsearch').setLevel(level=logging.ERROR)
    logging.getLogger('urllib3').setLevel(level=logging.ERROR)

    config = ConfigParser()
    config.read(arguments.get('<config>'))
    if arguments.get('ingester'):
        config['Ingester']['Password'] = arguments.get('<password>')
        run_ingester(config)
    else:
        run_server(config)
