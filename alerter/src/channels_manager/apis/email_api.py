import smtplib
from datetime import datetime
from email.message import EmailMessage, Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
        msg.set_content("{}\nDate - {}".format(message, datetime.now()))

        msg['Subject'] = subject
        msg['From'] = self._sender
        msg['To'] = to

        # Send the message via the specified SMTP server.
        self._send_smtp(msg)

    def send_email_with_html(self, subject: str, html_message: str,
                             plain_message: str, to: str) -> None:
        """
        <head> and <body> tags will be included here
        """
        html_wrapper = """\
        <html>
            <head></head>
            <body>
                {message}
                <p>Date - {timestamp}</p>
            </body>
        </html>"""

        msg = MIMEMultipart('alternative')

        msg['Subject'] = subject
        msg['From'] = self._sender
        msg['To'] = to

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText("{}\nDate - {}".format(plain_message, datetime.now()),
                         'plain')
        part2 = MIMEText(
            html_wrapper.format(message=html_message, timestamp=datetime.now()),
            'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this
        # case the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)

        self._send_smtp(msg)

    def _send_smtp(self, msg: Message) -> None:
        # Send the message via the specified SMTP server.
        s = smtplib.SMTP(self._smtp)
        if None not in [self._username, self._password] \
                and len(self._username) != 0:
            s.starttls()
            s.login(self._username, self._password)
        s.send_message(msg)
        s.quit()
