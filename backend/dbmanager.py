import logging
import re

import psycopg2 as psycopg2
import urllib.request
import html
import base64
from urllib.parse import quote


TAZENDRA_PDFS_LOCATION = "http://tazendra.caltech.edu/~acedb/daniel/"


logger = logging.getLogger(__name__)


class DBManager(object):

    def __init__(self, dbname, user, password, host):
        connection_str = "dbname='" + dbname
        if user:
            connection_str += "' user='" + user
        if password:
            connection_str += "' password='" + password
        connection_str += "' host='" + host + "'"
        self.conn = psycopg2.connect(connection_str)
        self.cur = self.conn.cursor()

    def close(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def get_variation_names_from_ids(self, ids: list):
        self.cur.execute("SELECT obo_name_variation FROM obo_name_variation WHERE joinkey IN ('{}')"
            .format("','".join(ids)))
        rows = self.cur.fetchall()
        var_names = [row[0] for row in rows]
        return set(var_names)

    def get_paper_pdf_path(self, paper_id):
        def get_tazendra_pdf_url(path):
            pdf_addr = path.replace('/home/acedb/daniel/Reference/wb/pdf/', TAZENDRA_PDFS_LOCATION).replace(
                '/home/acedb/daniel/Reference/pubmed/pdf/', TAZENDRA_PDFS_LOCATION).replace(
                '/home/acedb/daniel/Reference/pubmed/libpdf/', TAZENDRA_PDFS_LOCATION)
            if 'Reference/cgc/' in pdf_addr:
                pdf_addr = TAZENDRA_PDFS_LOCATION + '/' + pdf_addr.split('/')[-1]
            return pdf_addr
        self.cur.execute("SELECT pap_electronic_path FROM pap_electronic_path WHERE joinkey = '{}'".format(paper_id))
        rows = self.cur.fetchall()
        main_pdfs = []
        additional_pdfs = []
        for row in rows:
            if row[0].endswith(".pdf") and "supplemental" not in row[0]:
                if "_temp" in row[0] or "_ocr" in row[0] or "_lib" in row[0]:
                    additional_pdfs.append(get_tazendra_pdf_url(quote(row[0])))
                else:
                    main_pdfs.append(get_tazendra_pdf_url(quote(row[0])))
        if main_pdfs:
            return main_pdfs
        else:
            return additional_pdfs

