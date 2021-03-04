import os
import smtplib
from email.message import EmailMessage

#email address and password are stored as environment variables to be more secure
# EMAIL_ADDRESS = os.environ.get('WORK_EMAIL')
# EMAIL_PASSWORD = os.environ.get('WORK_APP_PASS')
EMAIL_ADDRESS = os.getenv('WORK_EMAIL')
EMAIL_PASSWORD = os.getenv('WORK_APP_PASS')
RECIEVER = '5305597263@vtext.com' # 5305597263@vzwpix.com

def send_text_message(to, message):
	msg = EmailMessage()
	msg['From'] = EMAIL_ADDRESS
	msg['To'] = to
	msg.set_content(message)
	# conencts to gmail server
	with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
		smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
		smtp.send_message(msg)
	print(f'Sent message to {to}')