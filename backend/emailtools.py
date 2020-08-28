import logging
import smtplib
import urllib.parse

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from urllib.request import urlopen


logger = logging.getLogger(__name__)


class EmailManager(object):

    def __init__(self, email_host, email_port, email_user, email_passwd):
        self.email_user = email_user
        self.server_host = email_host
        self.server_port = email_port
        self.email_passwd = email_passwd
        self.from_addr = email_user
        self.reply_to_addr = email_user

    def send_email(self, subject, content, recipient):
        body = MIMEText(content, "html")
        msg = MIMEMultipart('alternative')
        msg.attach(body)
        msg['Subject'] = subject
        msg['From'] = self.from_addr
        msg['reply-to'] = self.reply_to_addr
        msg['To'] = recipient
        try:
            server_ssl = smtplib.SMTP_SSL(self.server_host, self.server_port)
            server_ssl.login(self.email_user, self.email_passwd)
            server_ssl.send_message(msg)
            logger.info("Email sent to: " + recipient)
            server_ssl.quit()
        except:
            logger.fatal("Can't connect to smtp server. Email not sent.")
