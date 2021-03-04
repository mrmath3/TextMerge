import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from pytz import timezone

# define the scope
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name('TextMerge.json', scope)

# authorize the clientsheet 
client = gspread.authorize(creds)

# get the instance of the Spreadsheet(s)
student_info = client.open('Student Contact Information 2020 - 2021')
teacher_settings = client.open_by_url('https://docs.google.com/spreadsheets/d/1QQ0v71T-iEiSvZsJBAXpbozDkJ2uUhy2lTZHdSTrKAs')

# get the correct sheet of the Spreadsheet
mega_contact_table = student_info.worksheet("Mega Contact Table")

def get_settings(teacher_settings_sheet):
	# note: all values are strings by default (yes...even boolean and integers)
	# It is faster to just get all values from the sheet in 1 API call rather than 1 API call per setting
	all_sheet = teacher_settings_sheet.get_all_values()
	settings_dict = dict() # Initialize dictionary
	
	# Should a message be sent to the student? (boolean)
	contact_student = all_sheet[2][1] == 'TRUE'
	settings_dict['contact_student'] = contact_student
	
	# Should a message be sent to the parents & guardians? (boolean)
	contact_parent = all_sheet[3][1] == 'TRUE'
	settings_dict['contact_parent'] = contact_parent
	
	# Should an automated message be created depending on the grade of the student? (boolean)
	use_next_steps = all_sheet[8][1] == 'TRUE'
	settings_dict['use_next_steps'] = use_next_steps
	
	# Should a the messages be sent? (boolean)
	send_message = all_sheet[17][1] == 'TRUE'
	settings_dict['send_message'] = send_message
	
	# Get assignment numbers to check for low grades
	# Empty columns at the end are ignored (but not the middle)
	assignment_numbers = all_sheet[5]
	# The first column is the header which we don't need. Let's delete it
	del assignment_numbers[0]
	
	# Get threshold for each assignment number
	thresholds = all_sheet[6] 
	# Again delete the first header column
	del thresholds[0]

	# Delete any index in both 'assignment_numbers' and 'thresholds' wher assignment_numbers' element is blank
	# Let's find all the indices of the blank values first
	bad = [] # Initilize
	for elem in range(len(assignment_numbers)):
		if assignment_numbers[elem] == '':
			bad.append(elem)
	# Delete each of the bad columns
	# Delete from the end instead of the beginning, otherwise index messed up
	for elem in sorted(bad, reverse = True):
		del assignment_numbers[elem]
		del thresholds[elem]
	# Replace any remaining blanks in tresholds with 200
	for n, elem in enumerate(thresholds):
		if elem == '':
			thresholds[n] = '200'
	# Convert from strings to integers
	assignment_numbers[:] = [int(x) for x in assignment_numbers]
	thresholds[:] = [int(x) for x in thresholds]
	settings_dict['assignment_numbers'] = assignment_numbers
	settings_dict['thresholds'] = thresholds

	# Student Next Steps
	student_next_steps = []
	for row in range(6):
		next_step_row = []
		for col in range (3):
			next_step_row.append(all_sheet[10 + row][2 + col])
		# if low, high, or description blank, delete entire row
		if '' in next_step_row:
			print(f'Warning: In "Next Steps" for teacher settings import - Deleting {next_step_row} because of empty value')
		else:
			student_next_steps.append(next_step_row)
	settings_dict['student_next_steps'] = student_next_steps

	# Parent English Next Steps
	parent_en_next_steps = []
	for row in range(6):
		next_step_row = []
		for col in range (3):
			next_step_row.append(all_sheet[10 + row][10 + col])
		# if low, high, or description blank, delete entire row
		if '' in next_step_row:
			print(f'Warning: In "Next Steps" for teacher settings import - Deleting {next_step_row} because of empty value')
		else:
			parent_en_next_steps.append(next_step_row)
	settings_dict['parent_en_next_steps'] = parent_en_next_steps

	# Parent Spanish Next Steps
	parent_sp_next_steps = []
	for row in range(6):
		next_step_row = []
		for col in range (3):
			next_step_row.append(all_sheet[10 + row][18 + col])
		# if low, high, or description blank, delete entire row
		if '' in next_step_row:
			print(f'Warning: In "Next Steps" for teacher settings import - Deleting {next_step_row} because of empty value')
		else:
			parent_sp_next_steps.append(next_step_row)
	settings_dict['parent_sp_next_steps'] = parent_sp_next_steps

	return settings_dict

def get_new_row(teacher_log_sheet):
	# This will look though column A until there is a blank cell and return the number of that row (0 being the first row)
	row = 'heading'
	row_n = 0
	while row != None:
		row_n += 1
		row = teacher_log_sheet[0][row_n]
	return row_n

def write_log(teacher_log_sheet, student, receiver, cell, assign_check, message):
	# This will be an optional function after each individual message is sent out
	# Output: Time (Tue, 2/23/21 @ 3:30 PM); Reciever(Nina (Bob's Mom); Cell, Assignments checked, Assignments messaged, message
	# Assume log name is Teacher_Last_Name + 'Log' (i.e. Sindel -> Sindel Log)
	# get_all_values only returns non-empty cells. Therefore the length of the list + 1 is the next avaliable row
	row = len(teacher_log_sheet.get_all_values()) + 1
	t = datetime.now().astimezone(timezone("America/Los_Angeles")).strftime('%a, %-m/%d/%y @ %-I:%M%p')
	log_list = [t, student, receiver, cell, assign_check, message]
	teacher_log_sheet.update(f'A{row}:F{row}', [log_list])

# Get all student data
database = mega_contact_table.get_all_values()