import base64
import logging
import re
import shutil

import PyPDF2 as PyPDF2
from PyPDF2.generic import TextStringObject
from PyPDF2.pdf import ContentStream, b_, FloatObject, NumberObject
from PyPDF2.utils import u_
import urllib.request
import tempfile

from backend.dbmanager import DBManager

logger = logging.getLogger(__name__)


class NttExtractor(object):

    def __init__(self, tazendra_user, tazendra_passwd):
        self.tazendra_user = tazendra_user
        self.tazendra_passwd = tazendra_passwd

    def get_fulltext_from_paper_id(self, paper_id, db_manager: DBManager):
        def customExtractText(self):
            text = u_("")
            content = self["/Contents"].getObject()
            if not isinstance(content, ContentStream):
                content = ContentStream(content, self.pdf)
            # Note: we check all strings are TextStringObjects.  ByteStringObjects
            # are strings where the byte->string encoding was unknown, so adding
            # them to the text here would be gibberish.
            for operands, operator in content.operations:
                if operator == b_("Tj"):
                    _text = operands[0]
                    if isinstance(_text, TextStringObject):
                        text += _text
                elif operator == b_("T*"):
                    text += "\n"
                elif operator == b_("'"):
                    text += "\n"
                    _text = operands[0]
                    if isinstance(_text, TextStringObject):
                        text += operands[0]
                elif operator == b_('"'):
                    _text = operands[2]
                    if isinstance(_text, TextStringObject):
                        text += "\n"
                        text += _text
                elif operator == b_("TJ"):
                    for i in operands[0]:
                        if isinstance(i, TextStringObject):
                            text += i
                        elif isinstance(i, FloatObject) or isinstance(i, NumberObject):
                            if i < -100:
                                text += " "
                elif operator == b_("TD") or operator == b_("Tm"):
                    if len(text) > 0 and text[-1] != " " and text[-1] != "\n":
                        text += " "
            text = text.replace(" - ", "-")
            text = re.sub("\\s+", " ", text)
            return text

        def convert_pdf2text(pdf_url):
            pdf_fulltext = ""
            request = urllib.request.Request(pdf_url)
            base64string = base64.b64encode(bytes('%s:%s' % (self.tazendra_user, self.tazendra_passwd), 'ascii'))
            request.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))
            with urllib.request.urlopen(request) as response:
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    shutil.copyfileobj(response, tmp_file)
            try:
                pdf_reader = PyPDF2.PdfFileReader(open(tmp_file.name, 'rb'))
                for i in range(pdf_reader.numPages):
                    page_obj = pdf_reader.getPage(i)
                    page_obj.extractText = customExtractText
                    pdf_fulltext += page_obj.extractText(page_obj)
            except:
                pass
            return pdf_fulltext
        pdf_urls = db_manager.get_paper_pdf_path(paper_id)
        return "\n".join([convert_pdf2text(pdf_url) for pdf_url in pdf_urls])
