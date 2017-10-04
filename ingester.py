import base64
import logging
import requests


class Ingester:

    def __init__(self, url, password):
        self.logger = logging.getLogger(__name__)
        self.url = url
        self.encoded_password = base64.b64encode(
            password.encode()).decode('utf-8')

    def get_source(self):
        return self.url

    def ingest(self):
        header = {"Authentication": "Basic %s" % self.encoded_password}
        self.logger.info("Starting ingestion from '%s'", self.url)
        with requests.get(self.url, headers=header, timeout=30, stream=True) as r:
            for line in r.iter_lines():
                yield r.status_code, line.decode('utf-8')
        self.logger.info("Finished ingestion from '%s'", self.url)
