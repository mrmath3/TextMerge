import os
import smtplib
from email.message import EmailMessage

# email addresses and passwords are stored as environment variables to be more secure
# EMAIL_ADDRESS = os.getenv('WORK_EMAIL')
# EMAIL_PASSWORD = os.getenv('WORK_APP_PASS')

def send_text_message(to, message, teacher):
	# 'to' is a variable that is a gateway sms email that will end up sending a text message (thus no subject) (freecarrierlookup.com)
	# 'message' is the text message to send to the 'to' gateway sms email 
	# teacher is the identifier (last name recommended) that also matches the envireonment variables for e-mail and app password
	
	# Get e-mail address of teacher from environment variables
	EMAIL_ADDRESS = os.getenv(teacher + '_email') # note the formatting of what your enviroment variables should like like
	EMAIL_PASSWORD = os.getenv(teacher + '_app_pass') # note the formatting of what your environment variables should look like
	msg = EmailMessage()
	msg['From'] = EMAIL_ADDRESS
	msg['To'] = to
	msg.set_content(message)
	# conenct to gmail server...
	with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
		smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
		# ...and send the message
		smtp.send_message(msg)
	# print(f'Sent message to {to}') # optional to see if this is working correctly