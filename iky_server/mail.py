#!/usr/bin/env python
# title           :mail.py
# description     : Send,Receive and Parse Emails.
# author          :Alfred Francis , alfred.francis@pearldatadirect.com
# date            :18062016
# version         :0.1
# python_version  :2.7
# ==============================================================================
import imaplib
import smtplib
import sys
import email
from email.parser import Parser

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


class emailManager:
    def __init__(self, imapservername, smtpservername, username, password):
        self.imapServerName = imapservername
        self.userName = username
        self.passWord = password
        self.imapConnection = imaplib.IMAP4_SSL(self.imapServerName, 993)
        self.smtpConnection = smtplib.SMTP(smtpservername, 587)

    def openIMAP(self):
        try:
            (self.responseCode, capabilities) = self.imapConnection.login(self.userName,
                                                                          self.passWord)
        except:
            print sys.exc_info()[1]
            sys.exit(1)
        return self.responseCode

    def openSMTP(self):
        try:
            self.smtpConnection.starttls()
            self.smtpConnection.login(self.userName, self.passWord)
        except:
            print sys.exc_info()[1]
            sys.exit(1)
        return True

    def sendEmail(self, toAddress, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.userName
        msg['To'] = toAddress
        msg['Subject'] = subject

        body = body
        msg.attach(MIMEText(body, 'plain'))

        text = msg.as_string()
        self.smtpConnection.sendmail(self.userName, toAddress, text)

    def closeSMTP(self):
        return self.smtpConnection.quit()

    def closeIMAP(self):
        return self.imapConnection.close()

    def getUnReadMessages(self, emailSubject=""):
        parser = Parser()
        self.imapConnection.select(readonly=0)
        # responseCode, emails = self.imapConnection.search(None,'(UNSEEN SUBJECT "%s")' % emailSubject)
        responseCode, emails = self.imapConnection.search(None, '(UnSeen)')
        if responseCode == 'OK':
            for mailNumber in emails[0].split():
                responseCode, resultData = self.imapConnection.fetch(mailNumber, '(RFC822)')
                parsedEmail = parser.parsestr(resultData[0][1])
                singleMail = dict(parsedEmail)

                emailMsg = email.message_from_string(resultData[0][1])
                singleMail["body"] = ""

                if emailMsg.is_multipart():
                    for part in emailMsg.walk():
                        ctype = part.get_content_type()
                        cdispo = str(part.get('Content-Disposition'))

                        # skip any text/plain (txt) attachments
                        if ctype == 'text/plain' and 'attachment' not in cdispo:
                            singleMail["body"] = part.get_payload(decode=True)  # decode
                            break
                # not multipart - i.e. plain text, no attachments, keeping fingers crossed
                else:
                    singleMail["body"] = emailMsg.get_payload(decode=True)

                responseCode, resultData = self.imapConnection.uid('store',
                                                                   '542648', '+FLAGS', '(\\Seen)')
                yield singleMail

    def cleanEmail(self,dirtyMail):
        dirtyMail = dirtyMail.replace(r"\r\n", r"\n").replace(r"  ", r" ")
        result = ""
        for line in dirtyMail.splitlines():
            print ("#" + line + "#")
            line = line.strip()
            if (line.startswith('--')
                or line.startswith('From:')
                or line.startswith('Date:')
                or line.startswith('Subject:')
                or line.startswith('From:')
                or line.startswith('To:')
                or line.startswith('Cc:')
                or line.endswith('>,')
                or line.endswith('>')
                or line.endswith('<')
                or line.endswith(']')
                or line.startswith('>')
                or line.startswith('Requester')
                or line.startswith('Due by time')
                or line.startswith('Category')
                or line.startswith('Description')
                ):
                pass
            else:
                result += line + " "
        return result.strip()


if __name__ == '__main__':
    testEmail = emailManager("imap.gmail.com", "smtp.gmail.com", "ikytesting@gmail.com", "ikytesting999")
    testEmail.openIMAP()
    testEmail.openSMTP()
    while True:
        try:
            for singleMail in testEmail.getUnReadMessages():
                print("New Email from :" + singleMail["From"])

                cleanedEmailContent = testEmail.cleanEmail(singleMail["body"])

                with open("emails/"+singleMail["Date"]+".txt", "a") as myfile:
                    myfile.write(cleanedEmailContent)

                # r = requests.get("http://172.30.10.141/iky_parse?user_say=" + singleMail["body"])
                # body = "Hi,\n" + r.content + "\nCheers,\n\tiKY"
                #body = "Hi,\nYour query has been received.We'll get back to you soon\nCheers,\n\tiKY"
                #print(body)
                #testEmail.sendEmail(singleMail["From"], "Reply to your query", body)
        except KeyboardInterrupt:
            testEmail.closeIMAP()
            testEmail.closeSMTP()
            print "Connections terminated"
            sys.exit()
