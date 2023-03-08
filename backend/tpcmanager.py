import gzip
import json
import logging
import os
import ssl
import urllib.request

logger = logging.getLogger(__name__)


class TPCManager(object):
    def __init__(self, textpresso_api_token):
        self.textpresso_api_token = textpresso_api_token
        self.tpc_api_endpoint = "https://textpressocentral.org:18080/v1/textpresso/api/search_documents"
        self.tpc_api_endpoint_count = "https://textpressocentral.org:18080/v1/textpresso/api/get_documents_count"
        if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
            ssl._create_default_https_context = ssl._create_unverified_context

    def get_doc_count(self, keywords: list):
        """get count of papers in the C. elegans literature that mention any of the specified keywords
           from Textpresso Central API

        Args:
            keywords (list): the keywords to search
        Returns:
            int: the number of documents matching the query
        """
        data = json.dumps({"token": self.textpresso_api_token, "query": {
            "keywords": " ".join(keywords), "type": "document", "corpora": ["C. elegans"], "case_sensitive": True}})
        data = data.encode('utf-8')
        req = urllib.request.Request(self.tpc_api_endpoint_count, data, headers={'Content-type': 'application/json',
                                                                                 'Accept': 'application/json'})
        res = urllib.request.urlopen(req)
        logger.debug("Sending a document count request to Textpresso Central API")
        return int(json.loads(res.read().decode('utf-8')))

    def get_doc_matching_with_fulltext(self, keywords: list, start: int = 0, count: int = 200):
        """get list of papers in the C. elegans literature that mention any of the specified keywords
           from Textpresso Central API

        Args:
            keywords (list): the keywords to search
            start (int): optional, start from nth result
            count (int): optional, return up to nth result
        Returns:
            list: the documents matching the query
        """
        data = json.dumps({"token": self.textpresso_api_token, "query": {
            "keywords": " ".join(keywords), "type": "sentence", "corpora": ["C. elegans"], "since_num": start,
            "count": count, "case_sensitive": True}, "include_match_sentences": True})
        data = data.encode('utf-8')
        req = urllib.request.Request(self.tpc_api_endpoint, data, headers={'Content-type': 'application/json',
                                                                           'Accept': 'application/json'})
        res = urllib.request.urlopen(req)
        logger.debug("Sending a request to retrieve documents to Textpresso Central API")
        return [(doc["identifier"], doc["accession"], doc["title"] +
                 " ".join(doc["matched_sentences"])) for doc in json.loads(res.read().decode('utf-8'))]

    def get_doc_matching(self, keywords: list, start: int = 0, count: int = 200):
        """get list of papers in the C. elegans literature that mention any of the specified keywords
           from Textpresso Central API

        Args:
            keywords (list): the keywords to search
            start (int): optional, start from nth result
            count (int): optional, return up to nth result
        Returns:
            list: the documents matching the query
        """
        data = json.dumps({"token": self.textpresso_api_token, "query": {
            "keywords": " ".join(keywords), "type": "document", "corpora": ["C. elegans"], "since_num": start,
            "count": count, "case_sensitive": True}})
        data = data.encode('utf-8')
        req = urllib.request.Request(self.tpc_api_endpoint, data, headers={'Content-type': 'application/json',
                                                                           'Accept': 'application/json'})
        res = urllib.request.urlopen(req)
        logger.debug("Sending a request to retrieve documents to Textpresso Central API")
        return [(doc["identifier"], doc["accession"]) for doc in json.loads(res.read().decode('utf-8'))]

    def get_docid_matching(self, keywords: list, start: int = 0, count: int = 200):
        """get list of papers in the C. elegans literature that mention any of the specified keywords
           from Textpresso Central API

        Args:
            keywords (list): the keywords to search
            start (int): optional, start from nth result
            count (int): optional, return up to nth result
        Returns:
            list: the documents matching the query
        """
        data = json.dumps({"token": self.textpresso_api_token, "query": {
            "keywords": " ".join(keywords), "type": "document", "corpora": ["C. elegans"], "case_sensitive": True},
            "count": count, "since_num": start})
        data = data.encode('utf-8')
        req = urllib.request.Request(self.tpc_api_endpoint, data, headers={'Content-type': 'application/json',
                                                                           'Accept': 'application/json'})
        res = urllib.request.urlopen(req)
        logger.debug("Sending a request to retrieve documents to Textpresso Central API")
        return [doc["identifier"] for doc in json.loads(res.read().decode('utf-8'))]

    def get_doc_fulltext(self, accession):
        """get list of papers in the C. elegans literature that mention any of the specified keywords
           from Textpresso Central API

        Args:
            accession:
        Returns:
            list: the documents matching the query
        """
        data = json.dumps({"token": self.textpresso_api_token, "query": {
            "accession": accession[-15:], "type": "document", "corpora": ["C. elegans"]}, "include_all_sentences": True})
        data = data.encode('utf-8')
        req = urllib.request.Request(self.tpc_api_endpoint, data, headers={'Content-type': 'application/json',
                                                                           'Accept': 'application/json'})
        res = urllib.request.urlopen(req)
        logger.debug("Sending a fulltext request for " + accession[-15:])
        return [" ".join(doc["all_sentences"]) for doc in json.loads(res.read().decode('utf-8'))][0]

    @staticmethod
    def get_ids_from_wb_ftp():
        ret = []
        urllib.request.urlretrieve("ftp://ftp.ebi.ac.uk/pub/databases/wormbase/releases/WS277/species/c_elegans/PRJNA13758/annotation/c_elegans.PRJNA13758.WS277.knockout_consortium_alleles.xml.gz",
                                   "../ko_allelex.xml.gz")
        with gzip.open("../ko_allelex.xml.gz", 'rb') as f_in:
            for line in f_in:
                line = line.decode('utf-8')
                if "WBVar" in line:
                    ret.append(line.lstrip('<name>').rstrip('</name>\n'))
        return ret

