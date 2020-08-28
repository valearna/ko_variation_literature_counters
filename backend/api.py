#!/usr/bin/env python3

import argparse
import logging
import math

from gevent import monkey, spawn
monkey.patch_all()

from backend.emailtools import EmailManager
import falcon

from wsgiref import simple_server
from falcon import HTTPStatus
from backend.tpcmanager import TPCManager


NUM_KEYWORDS_EACH_API_CALL = 500


class HandleCORS(object):
    def process_request(self, req, resp):
        allow_headers = req.get_header(
            'Access-Control-Request-Headers',
            default='*'
        )
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', '*')
        resp.set_header('Access-Control-Allow-Headers', allow_headers)
        resp.set_header('Access-Control-Max-Age', 1728000)  # 20 days
        if req.method == 'OPTIONS':
            raise HTTPStatus(falcon.HTTP_200, body='\n')


def send_error_mail(variations, reply_to_addr, error, email_manager: EmailManager):
    email_manager.send_email("Error from TPC entity counter",
                             "An error occurred while calculating the statistics: " + str(error) +
                             "<br/><br/>Please contact the admin at "
                             "valearna@caltech.org<br/><br/>Input entities:<br/>" + "<br/>".join(variations),
                             reply_to_addr)


def get_total_count(variations: list, reply_to_addr: str, tpc_manager: TPCManager, email_manager: EmailManager):
    try:
        doc_ids = set()
        start = 0
        end = NUM_KEYWORDS_EACH_API_CALL
        while True:
            var_subset = variations[start:min(end, len(variations)) + 1]
            num_docs = tpc_manager.get_doc_count(var_subset)
            for i in range(0, math.ceil(num_docs / 200)):
                docs = tpc_manager.get_docid_matching(var_subset, start=i * 200)
                doc_ids.update(set(docs))
            if end > len(variations):
                break
            start = end + 1
            end += NUM_KEYWORDS_EACH_API_CALL
        email_manager.send_email("Results ready from TPC entity counter",
                                 "Total number of mentions in C. elegans literature: " + str(len(doc_ids)) + "<br/><br/>" +
                                 "Input entities:<br/>" + "<br/>".join(variations),
                                 reply_to_addr)
    except Exception as e:
        send_error_mail(variations, reply_to_addr, e, email_manager)


def get_vars_in_paper(variations: list, reply_to_addr: str, tpc_manager: TPCManager, email_manager: EmailManager):
    try:
        doc_id_accession_fulltext = {}
        start = 0
        end = NUM_KEYWORDS_EACH_API_CALL
        while True:
            var_subset = variations[start:min(end, len(variations)) + 1]
            num_docs = tpc_manager.get_doc_count(var_subset)
            for i in range(0, math.ceil(num_docs / 200)):
                docs = tpc_manager.get_doc_matching_with_fulltext(var_subset, start=i * 200)
                doc_id_accession_fulltext.update({doc[0]: (doc[1], doc[2]) for doc in docs})
            if end > len(variations):
                break
            start = end + 1
            end += NUM_KEYWORDS_EACH_API_CALL
        email_manager.send_email("Results ready from TPC entity counter",
                                 "Number of entities mentioned in each paper: <br/><br/>" +
                                 "<br/>".join([accession + "\t" + str(sum([fulltext.count(var) for var in variations])) for
                                               paper_id, (accession, fulltext) in doc_id_accession_fulltext.items()]) +
                                 "<br/><br/>" +
                                 "Input entities:<br/>" + "<br/>".join(variations),
                                 reply_to_addr)
    except Exception as e:
        send_error_mail(variations, reply_to_addr, e, email_manager)


def get_papersby_var(variations: list, reply_to_addr: str, tpc_manager: TPCManager, email_manager: EmailManager):
    try:
        email_manager.send_email("Results ready from TPC entity counter",
                                 "Number of papers mentioning each entity: <br/><br/>" +
                                 "<br/>".join([var_name + "\t" + str(tpc_manager.get_doc_count([var_name])) for
                                               var_name in variations]) +
                                 "<br/><br/>" +
                                 "Input entities:<br/>" + "<br/>".join(variations),
                                 reply_to_addr)
    except Exception as e:
        send_error_mail(variations, reply_to_addr, e, email_manager)


class TPCAPIReader:

    def __init__(self, tpc_manager: TPCManager, email_manager: EmailManager):
        self.tpc_manager = tpc_manager
        self.email_manager = email_manager
        self.logger = logging.getLogger(__name__)

    def on_post(self, req, resp):
        if "variations" in req.media and "replyto" in req.media:
            variations = req.media.get("variations")
            reply_to_addr = req.media.get("replyto")
            if req.media["type"] == "total_count":
                spawn(get_total_count, variations, reply_to_addr, self.tpc_manager, self.email_manager)
                #get_total_count(variations, reply_to_addr, self.tpc_manager, self.email_manager)
                resp.status = falcon.HTTP_OK
            elif req.media["type"] == "vars_in_paper":
                spawn(get_vars_in_paper, variations, reply_to_addr, self.tpc_manager, self.email_manager)
                resp.status = falcon.HTTP_OK
            elif req.media["type"] == "papers_per_var":
                spawn(get_papersby_var, variations, reply_to_addr, self.tpc_manager, self.email_manager)
                resp.status = falcon.HTTP_OK
        else:
            resp.status = falcon.HTTP_BAD_REQUEST


def main():
    parser = argparse.ArgumentParser(description="Find new documents in WormBase collection and pre-populate data "
                                                 "structures for Author First Pass")
    parser.add_argument("-l", "--log-file", metavar="log_file", dest="log_file", type=str, default=None,
                        help="path to the log file to generate. Default ./afp_pipeline.log")
    parser.add_argument("-L", "--log-level", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                                                        'CRITICAL'], default="INFO",
                        help="set the logging level")
    parser.add_argument("-t", "--tpc-token", metavar="tpc_token", dest="tpc_token", type=str, default="")
    parser.add_argument("-H", "--email-host", metavar="email_host", dest="email_host", type=str)
    parser.add_argument("-p", "--email-port", metavar="email_port", dest="email_port", type=str)
    parser.add_argument("-u", "--email-user", metavar="email_user", dest="email_user", type=str)
    parser.add_argument("-w", "--email-passwd", metavar="email_passwd", dest="email_passwd", type=str)
    parser.add_argument("-P", "--port", metavar="port", dest="port", type=int, help="API port")
    args = parser.parse_args()

    logging.basicConfig(filename=args.log_file, level=args.log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s:%(message)s')

    app = falcon.API(middleware=[HandleCORS()])
    tpc_manager = TPCManager(textpresso_api_token=args.tpc_token)
    email_manager = EmailManager(args.email_host, args.email_port, args.email_user, args.email_passwd)
    tpc_api_reader = TPCAPIReader(tpc_manager=tpc_manager, email_manager=email_manager)
    app.add_route('/get_stats', tpc_api_reader)

    httpd = simple_server.make_server('0.0.0.0', args.port, app)
    httpd.serve_forever()


if __name__ == '__main__':
    main()
else:
    import os
    app = falcon.API(middleware=[HandleCORS()])
    tpc_manager = TPCManager(textpresso_api_token=os.environ['TPC_TOKEN'])
    email_manager = EmailManager(os.environ['EMAIL_HOST'], os.environ['EMAIL_PORT'], os.environ['EMAIL_USER'],
                                 os.environ['EMAIL_PASSWD'])
    tpc_api_reader = TPCAPIReader(tpc_manager=tpc_manager, email_manager=email_manager)
    app.add_route('/get_stats', tpc_api_reader)
