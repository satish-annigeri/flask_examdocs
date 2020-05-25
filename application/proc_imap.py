from imaplib import IMAP4_SSL
import email
from email.parser import HeaderParser, BytesParser, Parser
import datetime as dt
import re
import sqlite3

### Class IMAP_Server ###

class IMAP_Server:
    def __init__(self, host, user, passwd):
        self.host = host
        self.user = user
        self.passwd = passwd
        try:
            self.imap = IMAP4_SSL(host)
            self.connected = True
        except:
            self.imap = None
            self.connected = False
        self.AUTH = False
        self.SELECTED = False
        self.mailboxes = None
        self.current_mailbox = None

    def login(self):
        if self.imap:
            typ, data = self.imap.login(self.user, self.passwd)
            if typ == 'OK':
                self.AUTH = True
                self.SELECTED = False

    def logout(self):
        if self.imap:
            if imap.SELECTED:
                self.imap.close()
                self.SELECTED = False
            if self.AUTH:
                self.imap.logout()
                self.AUTH = False
            self.imap = None
            self.connected = False
            self.mailboxes = None
            self.current_mailbox = None

    def select(self, mbox, readonly=True):
        if self.AUTH:
            typ, data = self.imap.select(mbox, readonly)
            if typ == 'OK':
                self.SELECTED = True
                self.current_mailbox = mbox
                return int(data[0].decode())

    def get_raw_message(self, msg_id):
        if self.SELECTED:
            typ, data = self.imap.fetch(msg_id, '(RFC822)')
            if typ == 'OK':
                raw_msg = data[0][1]
                return raw_msg
            else:
                return None

    def get_msg_ids(self, mbox=None):
        if not mbox is None:
            self.select(mbox)
        typ, data = self.imap.search(None, '(ALL)')
        return data[0].split()


### Regular expressions ###

re_ugusn = r'[1-9][A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{3}'
re_pgusn = r'[1-9][A-Z]{2}[0-9]{2}[A-Z]{3}[0-9]{2}'
re_payment_id = r'DU[A-Z][0-9]{7}'
re_amount = r'[0-9]+[.-]*[0-9]*'
re_phone = r'[+]*[0-9]{0,2}[0-9]{10}'
re_email = r'<\S+@\S+\.\S+>'

def get_usn(ln):
    if (s := re.search(re_ugusn, ln, re.I)):
        usn = ln[s.start():s.end()]
        usn_comment = ln + ' - Valid UG USN'
    elif (s := re.search(re_pgusn, ln, re.I)):
        usn = ln[s.start():s.end()]
        if usn[5] in ['P', 'p']:
            usn_comment = ln + ' - Ph.D. USN. Not accepted'
        else:
            usn_comment = ln + ' - Valid PG USN'
    else:
        usn = ln
        usn_comment = ln + ' - Invalid UG/PG USN'
    return usn, usn_comment


### Utility Functions ###

def get_date_time(date_str):
    try:
        ts = dt.datetime.strptime(date_str[:31], '%a, %d %B %Y %H:%M:%S %z').timestamp()
    except:
        print('Error: converting to date and time')
        return None, None
    date = dt.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    time = dt.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    return date, time


def get_name_email(header_email):
    s = re.search(re_email, header_email)
    if s:
        sender_name = header_email[:s.start()].strip()
        sender_email = header_email[s.start()+1:s.end()-1]
        return sender_name, sender_email
    else:
        return None, None

def get_text(msg):
    if msg.is_multipart():
        return get_text(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)


### Class RawMessage ###

class RawMessage:
    def __init__(self, raw_msg):
        self.raw_msg = raw_msg
        self.parse()

    def parse(self):
        b_parser = BytesParser()
        msg = b_parser.parsebytes(self.raw_msg)
        date_str = msg.get('Date')
        self.date, self.time = get_date_time(date_str)
        sender_str = msg.get('From')
        self.sender, self.sender_email = get_name_email(sender_str)
        self.subject = msg.get('Subject')
        self.body = get_text(msg)

        self.attachments = []
        if msg.get_content_maintype() == 'multipart':
            for part in msg.walk():
                if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                    attachment = {'fname': part.get_filename(), 'fcontent': part.get_payload(decode=True)}
                    self.attachments.append(attachment)

    def saveAttachments(self):
        if len(self.attachments) > 0:
            for att in self.attachments:
                usn = self.usn
                if len(usn) > 10:
                    usn = usn[:10]
                fname = f"{usn}_{att['fname']}"
                with open(fname, 'wb') as f:
                    f.write(att['fcontent'])
                    f.close()

    def get_payment_id(self, lines, body):
        i = 0
        while i < len(lines):
            if (len(lines) > 0) and (s := re.search(re_payment_id, lines[0], re.I)):
                self.payment_id = lines[0][s.start():s.end()]
                body.append(f'{lines[0]} - Valid payment ID')
                return i, body
            else:
                i += 1
        return None, None

    def analyse(self):
        self.usn, self.usn_comment = get_usn(self.subject)
        self.payment_id = ''
        self.amount = None
        self.phone = ''
        self.documents = ''
        lines = [ln for ln in self.body.decode().splitlines() if len(ln.strip()) > 0]
        body = []

        i, body = self.get_payment_id(lines, body)
        if i is None:
            return # Could not find a line with valid pyament_id

        if (len(lines) > i+1) and (s := re.search(re_amount, lines[i+1], re.I)):
            self.amount = lines[i+1][s.start():s.end()]
            body.append(f'{lines[1+1]} - Valid Fee amount')
        if (len(lines) > i+2) and (s := re.search(re_phone, lines[i+2], re.I)):
            self.phone = lines[i+2][s.start():s.end()]
            body.append(f'{lines[i+2]} - Valid Mobile number')
        if (len(lines) > i+3):
            self.documents = lines[i+3]
            body.append(lines[i+3])
        self.body = body

    def insert_db(self, sqlitedb):
        sql_msg = """INSERT INTO messages 
        (subject, sender, sender_email, date, time, usn, payment_id, amount, phone, documents,
        raw_msg) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        sql_att = "INSERT INTO attachments (filename, message_id) VALUES (?, ?)"
        conn = sqlite3.connect(sqlitedb)
        c = conn.cursor()
        c.execute(sql_msg, (
            self.subject, self.sender, self.sender_email, self.date, self.time, 
            self.usn, self.payment_id, self.amount, self.phone, self.documents, 
            self.raw_msg)
        )
        lastrowid = c.lastrowid
        for att in self.attachments:
            c.execute(sql_att, (att['fname'], lastrowid))
        conn.commit()
        c.close()
        conn.close()


if __name__ == '__main__':
    host = 'mail.vtu.ac.in'
    user = 'examdocs@vtu.ac.in'
    passwd = 'examdocs@2020'
    sqlite3_db = 'exdocs_emails.sqlite'

    imap = IMAP_Server(host, user, passwd)
    print(imap.connected)
    imap.login()
    print(imap.AUTH)
    mbox = 'Inbox'
    n = imap.select(mbox)
    print(f'{imap.current_mailbox} has {n} messages')

    msg_ids = imap.get_msg_ids()
    for msg_id in msg_ids:
        rmsg = RawMessage(imap.get_raw_message(msg_id))
        rmsg.analyse()
    # print(type(raw_msg), len(raw_msg))
    # rmsg = RawMessage(raw_msg)
        print(rmsg.date, rmsg.time, rmsg.sender, rmsg.subject, rmsg.sender_email)
    # print(rmsg.body)
        print('Attachments')
        for i, attachment in enumerate(rmsg.attachments):
            print('\t', i+1, attachment['fname'])
        print('-'*40)
        rmsg.insert_db(sqlite3_db)
    # usn, body = rmsg.analyse()
    # print(usn)
    # for ln in body:
    #     print(ln)
    # print('Saving attachments')
    # rmsg.saveAttachments()
    # print()

    imap.logout()
    print(imap.connected)
    print(imap.AUTH)
    