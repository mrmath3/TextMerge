import time, sched
main_start_time = time.time()
from google_sheets import database, teacher_settings, get_settings, write_log
from low_grades import get_low_grades
from send_text import send_text_message

# List of teachers to check (names should match the names of the tabs in the 'teacher settings' Google Spreadsheet)
teacher_list = [
	'Sindel'
]

# Should messages be printed to the console?
print_message = False
# This is mainly for testing purposes within the code
actually_send_text = False
# Should messages be logged to the Google Spreadsheet?
send_log = True
# How many minutes should the spreadsheets be checked?
wait = 5
wait *= 60 # this multiplies the previous value by 60 to convert into minutes

def get_next_step(percent, next_steps):
	# percentage is 1 value between 0 and 100
	# next_steps is a list of low, high, and next step
	for row in range(len(next_steps)):
		if percent >= float(next_steps[row][0]) and percent < float(next_steps[row][1]):
			return next_steps[row][2]

def list_to_string(list):
	string = str(list[0])
	if len(list) > 1:
		for elem in range(1, len(list)):
			string += ', ' + str(list[elem])
	return string

titles = {
	'dad' : 'Father',
	'mom' : 'Mother',
	'guardian' : 'Guardian',
	'student' : 'Student'
}

def function_statements(piece, parent_or_student, language, student_first_name, student_full, parent_type, individual_name, low_grades, low_student, nth_assignment):
	if piece == 'greeting':
		if parent_or_student == 'Student':
			if language == 'English': s = f'Hi {student_first_name}.\n'
			elif language == 'Spanish': s = f'Hola {student_first_name}.\n'
		elif parent_or_student == 'Parent':
			if language == 'English': s = f'Hi {individual_name}.\n'
			elif language == 'Spanish': s = f'Hola {individual_name}.\n'
	elif piece == 'assignment':
		if parent_or_student == 'Student':
			if language == 'English': s = f'You got a {low_grades[low_student][nth_assignment][1]:.0f}% on \"{low_grades[low_student][nth_assignment][0]}\". '
			elif language == 'Spanish': s = f'Recibiste un {low_grades[low_student][nth_assignment][1]:.0f}% en \"{low_grades[low_student][nth_assignment][0]}\". '
		elif parent_or_student == 'Parent':
			if language == 'English': s = f'{student_first_name} got a {low_grades[low_student][nth_assignment][1]:.0f}% on \"{low_grades[low_student][nth_assignment][0]}\". '
			elif language == 'Spanish': s = f'{student_first_name} recibió un {low_grades[low_student][nth_assignment][1]:.0f}% en \"{low_grades[low_student][nth_assignment][0]}\". '
	elif piece == 'recipient':
		if parent_or_student == 'Student': s = student_full
		elif parent_or_student == 'Parent': s = individual_name + ' (' + student_first_name + f'\'s {parent_type}' + ')'
	return s

statements = {
	'next_steps': {
		'Student' : {
			'English' : 'student_next_steps',
			'Spanish' : 'student_next_steps' # wait until update to interface to add this
		},
		'Parent' : {
			'English' : 'parent_en_next_steps',
			'Spanish' : 'parent_sp_next_steps'
		}
	},
	'contact': {
		'Student' : {
			'English' : '\nFeel free to text me back if you have any questions or concerns.',
			'Spanish' : '\nEnvíeme un mensaje si tiene alguna pregunta'
		},
		'Parent' : {
			'English' : '\nFeel free to text me back if you have any questions or concerns.',
			'Spanish' : '\nEnvíeme un mensaje si tiene alguna pregunta'
		}
	}
}

def custom_message(parent_type, poss_student, database, low_grades, low_student, settings, log, assign_check, teacher):
	title = titles[parent_type]
	student_first_name = database[poss_student][database[0].index('Student\'s First Name')]
	student_last_name = database[poss_student][database[0].index('Student\'s Last Name')]	
	student_full = student_first_name + ' ' + student_last_name
	parent_or_student = 'Student' if parent_type == 'student' else 'Parent'
	nth_assignment = 0 # temporary nth_assignment to make function_statements work
	# Check if phone number is on file
	if database[poss_student][database[0].index(f'{title}\'s Cell SMS')] != '':
		language = database[poss_student][database[0].index(f'{title}\'s Language')]
		cell = database[poss_student][database[0].index(f'{title}\'s Cell')]
		individual_name = database[poss_student][database[0].index(f'{title}\'s First Name')]
		# Greeting
		message = function_statements('greeting', parent_or_student, language, student_first_name, student_full, parent_type, individual_name, low_grades, low_student, nth_assignment)
		# Assignments information
		for nth_assignment in range(1, len(low_grades[low_student])): # add 1 to not grab student's name
			message += function_statements('assignment', parent_or_student, language, student_first_name, student_full, parent_type, individual_name, low_grades, low_student, nth_assignment)
			# Next steps
			if settings['use_next_steps'] == True:
				message += get_next_step(low_grades[low_student][nth_assignment][1], settings[statements['next_steps'][parent_or_student][language]])
				message += ' '
		# Contact me
		message += statements['contact'][parent_or_student][language]
		if print_message == True: print(message)
		if actually_send_text == True: send_text_message(database[poss_student][database[0].index(f'{title}\'s Cell SMS')], message, teacher)
		recipient = function_statements('recipient', parent_or_student, language, student_first_name, student_full, parent_type, individual_name, low_grades, low_student, nth_assignment)
		if send_log == True: write_log(log, student_full, recipient, cell, assign_check, message)

def textMerge(teacher):
	# the input for this function needs to be the name of the tab in Google Sheets for the teacher
	settings = get_settings(teacher_settings.worksheet(teacher))
	if settings['send_message'] == True:
		function_start_time = time.time()
		log = teacher_settings.worksheet(teacher + ' Log')
		low_grades = get_low_grades(settings['assignment_numbers'], settings['thresholds'])
		assign_check = list_to_string(settings['assignment_numbers']) # What assignment numbers are checked?
		for low_student in range(len(low_grades)):
			# scan each column in database trying to get a match
			for poss_student in range(len(database)):
				# Check each possible student against the aeries identifier in the database
				if low_grades[low_student][0] == database[poss_student][database[0].index('Aeries Identifier')]:
					# Should guardians be messaged?
					if (settings['contact_parent'] == True):
						custom_message('dad', poss_student, database, low_grades, low_student, settings, log, assign_check, teacher)
						custom_message('mom', poss_student, database, low_grades, low_student, settings, log, assign_check, teacher)
						custom_message('guardian', poss_student, database, low_grades, low_student, settings, log, assign_check, teacher)
					# Should student be messaged?
					if (settings['contact_student'] == True):
						# Send a message to the student
						# Check if student's phone number is on file
						if database[poss_student][database[0].index('Student\'s Cell SMS')] != None:
							custom_message('student', poss_student, database, low_grades, low_student, settings, log, assign_check, teacher)
		# Uncheck the 'Send Messages?' Box in teacher settings
		teacher_settings.worksheet(teacher).update('B18', False)
		if print_message == True: print('--------------------------------')
		print(f'Successfully ran textMerge for {teacher} in {(time.time() - function_start_time):.2f} seconds.')

def check_teachers(sc, teacher_list):
	check_time = time.time()
	for teacher in teacher_list:
		print(f'Checking {teacher}...')
		textMerge(teacher)
	print(f'Completed check in {(time.time() - check_time):.2f} seconds. Waiting {(wait / 60):.0f} minutes until the next check.')
	s.enter(wait, 1, textMerge, (sc, teacher_list))

print(f'Running TextMerge for the following list of teachers: {list_to_string(teacher_list)}.')
s = sched.scheduler(time.time, time.sleep)
s.enter(0, 1, check_teachers, (s,teacher_list))
s.run()

# print(f'TextMerge took {(time.time() - main_start_time):.2f} seconds to run')