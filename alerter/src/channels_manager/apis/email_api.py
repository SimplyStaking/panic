import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Optional


class EmailApi:

    def __init__(self, smtp: str, sender: str, username: Optional[str],
                 password: Optional[str]) -> None:
        super().__init__()

        # If blank/None username or None password, EmailSender assumes
        # that these are both blank and that no authentication is required

        self._smtp = smtp
        self._sender = sender
        self._username = username
        self._password = password

    def send_email(self, subject: str, message: str, to: str) -> None:
        msg = EmailMessage()
        msg.set_content('{}\nDate - {}'.format(message, datetime.now()))

        msg['Subject'] = subject
        msg['From'] = self._sender
        msg['To'] = to

        # Send the message via the specified SMTP server.
        s = smtplib.SMTP(self._smtp)
        if None not in [self._username, self._password] \
                and len(self._username) != 0:
            s.starttls()
            s.login(self._username, self._password)
        s.send_message(msg)
        s.quit()
