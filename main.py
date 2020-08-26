#!/usr/bin/env python3

import logging
import argparse
import math

from apimanager import APIManager
from dbmanager import DBManager

logger = logging.getLogger(__name__)

NUM_KEYWORDS_EACH_API_CALL = 500


def main():
    parser = argparse.ArgumentParser(description="Send reminder emails to authors who have not submitted their data to "
                                                 "AFP")
    parser.add_argument("-N", "--db-name", metavar="db_name", dest="db_name", type=str)
    parser.add_argument("-U", "--db-user", metavar="db_user", dest="db_user", type=str)
    parser.add_argument("-P", "--db-password", metavar="db_password", dest="db_password", type=str)
    parser.add_argument("-H", "--db-host", metavar="db_host", dest="db_host", type=str)
    parser.add_argument("-t", "--textpresso-apitoken", metavar="tpc_token", dest="tpc_token", type=str)
    parser.add_argument("-l", "--log-file", metavar="log_file", dest="log_file", type=str, default=None,
                        help="path to the log file to generate. Default ./afp_pipeline.log")
    parser.add_argument("-L", "--log-level", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                                                        'CRITICAL'], default="INFO",
                        help="set the logging level")

    args = parser.parse_args()
    logging.basicConfig(filename=args.log_file, level=args.log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s:%(message)s')

    db_manager = DBManager(dbname=args.db_name, user=args.db_user, password=args.db_password, host=args.db_host)
    api_manager = APIManager(args.tpc_token)
    var_names = list(db_manager.get_variation_names_from_ids(api_manager.get_ids_from_wb_ftp()))
    doc_id_fulltext = {}
    start = 1
    end = NUM_KEYWORDS_EACH_API_CALL
    while True:
        num_docs = api_manager.get_doc_count(var_names[start:min(end, len(var_names)) + 1])
        for i in range(0, math.ceil(num_docs / 200)):
            docs = api_manager.get_doc_matching(var_names[start:min(end, len(var_names)) + 1], start=i * 200)
            doc_id_fulltext.update({doc[0]: (doc[1], doc[2]) for doc in docs})
        if end > len(var_names):
            break
        start = end + 1
        end += NUM_KEYWORDS_EACH_API_CALL
    print("Total number of mentions:" + str(len(doc_id_fulltext)))
    print()
    print("Number of KO variations mentioned in each paper:")
    for paper_id, (accession, fulltext) in doc_id_fulltext.items():
        print(paper_id.split("/")[1], accession, str(sum([fulltext.count(var) for var in var_names])), sep="\t")
    print()
    print("Mentions by variation")
    for var_name in var_names:
        print(var_name, str(api_manager.get_doc_count([var_name])), sep="\t")
    db_manager.close()


if __name__ == '__main__':
    main()
