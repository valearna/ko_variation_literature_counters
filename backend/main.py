#!/usr/bin/env python3

import logging
import argparse
import math

from backend.tpcmanager import TPCManager
from backend.dbmanager import DBManager
from backend.nttxtraction import NttExtractor

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
    parser.add_argument("-w", "--tazendra-username", metavar="tazendra_user", dest="tazendra_user", type=str)
    parser.add_argument("-z", "--tazendra-password", metavar="tazendra_password", dest="tazendra_password", type=str)
    parser.add_argument("-l", "--log-file", metavar="log_file", dest="log_file", type=str, default=None,
                        help="path to the log file to generate. Default ./afp_pipeline.log")
    parser.add_argument("-o", "--output-type", dest="output_type",
                        choices=['TOTAL_COUNT', 'VAR_COUNT_IN_PAPERS', 'PAPER_COUNT_FOR_VAR'], default="TOTAL_COUNT",
                        help="type of count to calculate")
    parser.add_argument("-L", "--log-level", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                                                        'CRITICAL'], default="INFO",
                        help="set the logging level")

    args = parser.parse_args()
    logging.basicConfig(filename=args.log_file, level=args.log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s:%(message)s')

    db_manager = DBManager(dbname=args.db_name, user=args.db_user, password=args.db_password, host=args.db_host)
    ntt_xtractor = NttExtractor(args.tazendra_user, args.tazendra_password)
    api_manager = TPCManager(args.tpc_token)
    var_names = list(db_manager.get_variation_names_from_ids(api_manager.get_ids_from_wb_ftp()))
    if args.output_type == "TOTAL_COUNT" or args.output_type == "VAR_COUNT_IN_PAPERS":
        doc_id_accession = {}
        start = 1
        end = NUM_KEYWORDS_EACH_API_CALL
        while True:
            num_docs = api_manager.get_doc_count(var_names[start:min(end, len(var_names)) + 1])
            for i in range(0, math.ceil(num_docs / 200)):
                docs = api_manager.get_doc_matching(var_names[start:min(end, len(var_names)) + 1], start=i * 200)
                doc_id_accession.update({doc[0]: doc[1] for doc in docs})
            if end > len(var_names):
                break
            start = end + 1
            end += NUM_KEYWORDS_EACH_API_CALL
        if args.output_type == "TOTAL_COUNT":
            print("Total number of mentions:" + str(len(doc_id_accession)))
        elif args.output_type == "VAR_COUNT_IN_PAPERS":
            for paper_id, accession in doc_id_accession.items():
                fulltext = ntt_xtractor.get_fulltext_from_paper_id(accession[-8:], db_manager)
                if fulltext:
                    counter = sum([fulltext.count(var) for var in var_names])
                else:
                    counter = "NA"
                print(accession.strip(" ").replace("Other:", "").replace("\\", ""), str(counter), sep="\t")
    elif args.output_type == "PAPER_COUNT_FOR_VAR":
        for var_name in var_names:
            print(var_name, str(api_manager.get_doc_count([var_name])), sep="\t")


if __name__ == '__main__':
    main()
