from imaplib import IMAP4_SSL
import email
from email.parser import HeaderParser, BytesParser, Parser
import datetime as dt
import re


def get_date_time(date_str):
    try:
        ts = dt.datetime.strptime(date_str[:31], '%a, %d %B %Y %H:%M:%S %z').timestamp()
    except:
        print('Error: converting to date and time')
    date = dt.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    time = dt.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    return date, time


re_usn = r'[1-9][A-Z]{2}[0-9]{2}[A-Z]{2,3}[0-9]{2,3}'
re_payment_id = r'DU[A-Z][0-9]{7}'
re_amount = r'[0-9]+[.-]*[0-9]*'
re_phone = r'[+]*[0-9]{0,2}[0-9]{10}'

def get_usn(ln):
    s = re.search(re_usn, ln, re.I)
    if s:
        usn = ln[s.start():s.end()]
        if usn[5] in ['P', 'p']:
            usn = ln + ' - Research student'
    else:
        usn = ln + ' - Incorrect UG/PG USN'
    return usn

def get_text(msg):
    if msg.is_multipart():
        return get_text(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)

# =========== IMAP4 Server class ===========

class IMAP_Server:
    def __init__(self, host, user, passwd):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.imap = None
        self.current_folder = None
        self.get_folder_list()

    def __repr__(self):
        return f'<IMAP Server host = {self.host} has {len(self.folders)} folders>'

    def login(self, folder=''):
        if self.imap:
            return
        try:
            self.imap = IMAP4_SSL(self.host)
            self.imap.login(user, passwd)
            if folder:
                self.select(folder)
        except Exception as e:
            self.imap = None

    def logout(self):
        if self.current_folder:
            self.imap.close()
            self.current_folder = None
        self.imap.logout()
        self.imap = None

    def select(self, folder='INBOX'):
        res, data = self.imap.select(folder)
        if res == 'OK':
            self.current_folder = folder
        else:
            self.current_folder = None

    def get_folder_list(self):
        self.login()
        _, folders = self.imap.list()
        self.folders = [folder.decode().split()[-1] for folder in folders]
        self.logout()

    def get_msg_ids(self, folder='INBOX'):
        self.login(folder)
        res, msg_ids = self.imap.search(None, 'ALL')
        if res == 'OK':
            msg_ids = msg_ids[0].split()
        else:
            msg_ids = None
        self.logout()
        return msg_ids

    def get_msg_header(self, folder, msg_id):
        self.login()
        self.select(folder)
        res, data = self.imap.fetch(msg_id, '(BODY[HEADER.FIELDS (FROM DATE SUBJECT)])')
        if res == 'OK':
            header = data[0][1].decode()
            parser = HeaderParser()
            msg = parser.parsestr(header)
            email_from = msg.get('From')
            date_str = msg.get('Date')
            date, time = get_date_time(date_str)
            subject = msg.get('Subject')
            att_fnames = self.get_attachment_fnames(folder, msg_id)
            header_data = {'email_from': email_from, 'date': date, 'time': time, 'subject': subject, 'attachment_fnames': att_fnames}
            return header_data
        else:
            print('Error fetching message header')
            return None

    def get_msg_body(self, folder, msg_id):
        print(f'Message ID: {msg_id}')
        self.login()
        self.select(folder)
        _, data = self.imap.fetch(msg_id, '(RFC822)')
        parser = BytesParser()
        msg = parser.parsebytes(data[0][1])
        date_str = msg.get('Date')
        date, time = get_date_time(date_str)
        body = get_text(msg)
        # body = body.decode().replace('\r', '').splitlines()
        # body = [ln for ln in body if len(ln.strip()) > 0]
        # email_msg = {'email_from': msg.get('From'), 'date': date, 'time': time, 'subject': msg.get('Subject'), 'body': body}
        # self.logout()
        return body.decode()

    def get_attachment_fnames(self, folder, msg_id):
        # self.login(folder)

        res, data = self.imap.select(folder, True)
        if res == 'OK':
            res, data = self.imap.fetch(msg_id, "(BODY.PEEK[])")
            email_body = email.message_from_bytes(data[0][1])
            if email_body.get_content_maintype() != 'multipart':
                return None
            attachment_fnames = []
            for part in email_body.walk():
                if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                    attachment_fnames.append(part.get_filename())
            # self.logout()
            return attachment_fnames            
        else:
            # self.logout()
            return None

    def get_message(self, folder, msg_id):
        self.login()
        self.select(folder)
        header = self.get_msg_header(folder, msg_id)
        body = self.get_msg_body(folder, msg_id)
        self.logout()
        return {'header': header, 'body': body}

    def get_headers(self, folder='INBOX'):
        msg_ids = self.get_msg_ids(folder)
        self.login(folder)
        self.select(folder)

        message_headers = []
        for msg_id in msg_ids:
            header = self.get_msg_header(folder, msg_id)
            if header:
                message_headers.append(header)
            else:
                print('Error:', data[0][1])
                return None
        self.logout()
        return message_headers


host = 'mail.vtu.ac.in'
user = 'examdocs@vtu.ac.in'
passwd = 'examdocs@2020'


if __name__ == '__main__':
    imap = IMAP_Server(host, user, passwd)
    print(imap)
    print(imap, type(imap.folders))
    for folder in imap.folders:
        print(folder)
    
    folder = 'INBOX'
    msg_ids = imap.get_msg_ids(folder)
    print(f'Messages in {folder} folder: {len(msg_ids)}')
    msg = imap.get_message(folder, msg_ids[0])
    print(msg['header'])
    print(msg['body'])
    # for msg_id in msg_ids:
    #     header = imap.get_msg_header(folder, msg_id)
    #     print(f'Message ID: {msg_id}', end=' ')
    #     print(header)
    # msg_headers = imap.get_headers(folder)
    # for i, msg_hdr in enumerate(msg_headers):
    #     print(i+1, msg_hdr)

    # for msg_id in msg_ids:
    #     msg = imap.get_msg_body(folder, msg_id)
    #     # print(msg['email_from'], msg['subject'])
    #     # print(msg['body'])
    #     usn = get_usn(msg['subject'])
    #     print(msg['date'], msg['time'], msg['email_from'], usn, msg['body'][0])
