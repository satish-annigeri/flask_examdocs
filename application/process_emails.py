import sys
import re
import datetime as dt

from pathlib import Path
from jinja2.nativetypes import NativeEnvironment, NativeTemplate 

from imap_tools import MailBox, Q
from imaplib import IMAP4_SSL
import email
from email.parser import HeaderParser

# from .models import Message

re_usn = r'[1-9][A-Z]{2}[0-9]{2}[A-Z]{2,3}[0-9]{2,3}'
re_payment_id = r'[A-Z]{3}[0-9]{7}'
re_amount = r'[0-9]+[.-]*[0-9]*'
re_phone = r'[+]*[0-9]{0,2}[0-9]{10}'

host = 'mail.vtu.ac.in'
user = 'examdocs@vtu.ac.in'
passwd = 'examdocs@2020'
folder = 'INBOX'

class mas_id:
    def __init__(self, msg):
        self.uid = msg.uid
        self.email_from = msg.from_
        self.date = msg.date
        subject = msg.subject
        text = self.get_text(msg)
        self.parse_data(subject, text)
        self.get_attachments(msg)

    def __repr__(self):
        s = f'<uid: {self.uid}, From: {self.email_from} {self.date} {self.usn}>\n'
        s += f'{self.payment_id} {self.amount} {self.phone} {self.doc_type}'
        return s

    def get_text(self, msg):
        text = msg.text.replace('\r', '').splitlines()
        text = [ln.strip() for ln in text]
        text = [ln for ln in text if len(ln) > 0]
        return text

    def get_usn(self, subject):
        subject = subject.strip()
        m = re.search(re_usn, subject, re.I)
        if m:
            usn = subject[m.start():m.end()]
            if usn[5] == '5':
                self.usn = usn + ' - Research student'
            else:
                self.usn = usn
        else:
            self.usn = subject + ' - Incorrect UG/PG USN'

    def get_payment_id(self, text):
        if len(text) < 1:
            self.payment_id = 'Payment ID not specified'
            return
        m = re.search(re_payment_id, text[0], re.I)
        if m:
            self.payment_id = text[0][m.start():m.end()].upper()
        else:
            self.payment_id = text[0] + ' - Incorrect payment id'

    def get_amount(self, text):
        if len(text) < 2:
            self.amount = 'Amount not specified'
            return
        m = re.search(re_amount, text[1], re.I)
        if m:
            self.amount = text[1][m.start():m.end()].upper()
        else:
            self.amount = text[1] + ' - Incorrect amount'

    def get_phone(self, text):
        if len(text) < 3:
            self.phone = 'Phone number not specified'
            return
        m = re.search(re_phone, text[2], re.I)
        if m:
            self.phone = text[2][m.start():m.end()].upper()
        else:
            self.phone = text[2]

    def get_doc_type(self, text):
        if len(text) < 4:
            self.doc_type = 'Document type not specified'
            return
        self.doc_type = text[3]

    def parse_data(self, subject, text):
        self.get_usn(subject)
        self.get_payment_id(text)
        self.get_amount(text)
        self.get_phone(text)
        self.get_doc_type(text)

    def get_attachments(self, msg):
        attachments = msg.attachments
        if len(attachments) == 0:
            self.attachments = 'No attachments'
            return
        self.attachments = []
        for att in attachments:
            fname = att.filename
            fpath = Path(fname)
            if fpath.suffix.lower() == '.pdf':
                self.attachments.append(f'{fname}')
            else:
                self.attachments.append(f'{fname} - Not in PDF format')

    def downloadAttachments(self, mas_id, pathToSaveFile):
        """
        Save Attachments to pathToSaveFile (Example: pathToSaveFile = "C:\\Program Files\\")
        """
        att_path_list = []
        for part in mas_id.walk():
            # multipart are just containers, so we skip them
            if part.get_content_maintype() == 'multipart':
                continue

            # is this part an attachment ?
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()

            att_path = os.path.join(pathToSaveFile, filename)

            #Check if its already there
            if not os.path.isfile(att_path) :
                # finally write the stuff
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()
            att_path_list.append(att_path)
        return att_path_list


def get_messages(host, user, password, folder):
    mbox = MailBox(host)
    mbox.login(user, password, initial_folder=folder)
    messages = [msg for msg in mbox.fetch()]
    return messages

def get_num_messages(folder):
    try:
        M = IMAP4_SSL(host)
    except Exception as e:
        return None
    res, data = M.login(user, passwd)
    if res == 'OK':
        res, data = M.select(folder, True)
        if res == 'OK':
            res, data = M.search(None, 'ALL')
            M.close()
            M.logout()
            return len(data[0].split())
        else:
            return None
    else:
        return None


def get_attachment_fnames(folder, msg_id):
    try:
        M = IMAP4_SSL(host)
    except Exception as e:
        return None
    res, data = M.login(user, passwd)
    if res == 'OK':
        res, data = M.select(folder, True)
        if res == 'OK':
            res, data = M.fetch(msg_id, "(BODY.PEEK[])")
            email_body = email.message_from_bytes(data[0][1])
            if email_body.get_content_maintype() != 'multipart':
                return None
            attachment_fnames = []
            for part in email_body.walk():
                if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                    attachment_fnames.append(part.get_filename())
            return attachment_fnames            
        else:
            return None
    else:
        return None


def get_message_ids(folder):
    try:
        M = IMAP4_SSL(host)
    except Exception as e:
        return None
    res, data = M.login(user, passwd)
    if res == 'OK':
        res, data = M.select(folder, True)
        res, data = M.search(None, '(ALL)')
        return data[0].split()
    else:
        return None


def get_message_summary(folder):
    try:
        M = IMAP4_SSL(host)
    except Exception as e:
        return None
    res, data = M.login(user, passwd)
    if res == 'OK':
        res, data = M.select(folder, True)
        if res == 'OK':
            res, data = M.search(None, 'ALL')
            msg_ids = data[0].split()
            message_headers = []
            for msg_id in msg_ids:
                res, data = M.fetch(msg_id, '(BODY[HEADER.FIELDS (FROM DATE SUBJECT)])')
                if res == 'OK':
                    header = data[0][1].decode()
                    parser = HeaderParser()
                    msg = parser.parsestr(header)
                    email_from = msg.get('From')
                    date_str = msg.get('Date')
                    timestamp = dt.datetime.strptime(date_str, '%a, %d %B %Y %H:%M:%S %z').timestamp()
                    date = dt.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                    time = date = dt.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
                    subject = msg.get('Subject')
                    message_headers.append((email_from, date, time, subject))
                else:
                    print('Error:', data[0][1])
                    return None
            return message_headers
    M.close()
    M.logout()


def gen_report(email_msg, tpl_file='ack.txt'):
    with open(tpl_file, 'r') as f:
        tpl_string = f.read()
    env = NativeEnvironment()
    tpl = env.from_string(tpl_string)
    report = tpl.render(data=email_msg)
    return report


if __name__ == '__main__':
    folder = 'error'
    msg_ids = get_message_ids(folder)
    for msg_id in msg_ids:
        print('Message ID:', msg_id)
        att_fnames = get_attachment_fnames(folder, msg_id)
        for fn in att_fnames:
            print('\t', fn)
        print()

    # n = get_num_messages('INBOX')
    # print(n)
    # msg_h = get_message_summary('INBOX')
    # for msg in msg_h:
    #     print(msg)

    # mbox = MailBox(host)
    # mbox.login(user, passwd, initial_folder=folder)
    # print(f'Selecting folder: {folder}')
    # messages = get_messages(host, user, passwd, folder)
    # # msg = messages[5]
    # # print(mas_id(msg))
    # for msg in messages:
    #     m = mas_id(msg)
    #     # print(m)
    #     print(m.attachments)
    #     # print(gen_report(m))
    #     print('-'*50)