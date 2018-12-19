from flask_wtf import FlaskForm, RecaptchaField, Recaptcha
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SubmitField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Optional, Email, ValidationError, EqualTo, Length
from avr.models import Admin, User, Student, ProposedProject, Project, Supervisor

class RegistrationForm(FlaskForm):
	firstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	lastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	firstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	lastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])

	studentId = StringField('ID', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])

	academicStatus = SelectField('Academic Status', choices=[('ug', 'UG'), ('msc', 'MSc'), ('phd', 'PhD'), ('guest', 'Guest'), ('research-fellow', 'Research Fellow'), ('other', 'Other')], default="ug")
	faculty = SelectField('Faculty', choices=[('Computer Science', 'Computer Science'), ('Electrical Engineering', 'Electrical Engineering'), ('Mechanical Engineering', 'Mechanical Engineering'), ('Medical Engineering', 'Medical Engineering'), ('Other', 'Other')], default="Computer Science")
	cellPhone = StringField('Cell Phone')
	email = StringField('Email', validators=[DataRequired(), Email()])
	semester = SelectField('Semester')
	year = SelectField('Year')
	projectTitle = SelectField('Project Title')
	profilePic = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
	recaptcha = RecaptchaField(validators=[Recaptcha(message="Click the checkbox above to verify you are a human!")])
	submit = SubmitField('Register')

	
	def validate_firstNameHeb(self, firstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in firstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_lastNameHeb(self, lastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in lastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_firstNameEng(self, firstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in firstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_lastNameEng(self, lastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in lastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')
	
	def validate_cellPhone(self, cellPhone):
		if any(c.isalpha() for c in cellPhone.data):
			raise ValidationError('Not a valid cell phone number!')

	def validate_studentId(self, studentId):
		if not studentId.data.isdigit():
			raise ValidationError('Must contain only numbers!')
		else :
			student = Student.query.filter_by(studentId=studentId.data).first()
			if student:
				raise ValidationError('This student is already registred!')
			user = User.query.filter_by(userId=studentId.data).first()
			if user:
				raise ValidationError('A user with this ID is already registred!')
	
	def validate_email(self, email):
			student = Student.query.filter_by(email=email.data).first()
			if student:
				raise ValidationError('This email is already used by another student!')

class createAdminForm(FlaskForm):
	id = StringField('ID', validators=[DataRequired()], render_kw={"placeholder": "ID"})
	password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Password"})
	confirmPassword = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"placeholder": "Confirm Password"})
	submitForm = SubmitField('Create Account')

	def validate_id(self, id):
		if not id.data.isdigit():
				raise ValidationError('Must contain only numbers!')
		else:
			admin = Admin.query.filter_by(adminId=id.data).first()
			if admin:
				raise ValidationError('This admin is already registred!')

class LoginForm(FlaskForm):
	id = StringField('ID', validators=[DataRequired()], render_kw={"placeholder": "ID"})
	password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Password"})
	#recaptcha = RecaptchaField(validators=[Recaptcha(message="Click the checkbox above to verify you are a human!")])
	submitLoginForm = SubmitField('Login')

class EditAccountForm(FlaskForm):
	studentId = StringField('ID', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
	firstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	lastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	firstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	lastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])
	academicStatus = SelectField('Academic Status', choices=[('ug', 'UG'), ('msc', 'MSc'), ('phd', 'PhD'), ('guest', 'Guest'), ('research-fellow', 'Research Fellow'), ('other', 'Other')], default="ug")
	faculty = SelectField('Faculty', choices=[('Computer Science', 'Computer Science'), ('Electrical Engineering', 'Electrical Engineering'), ('Mechanical Engineering', 'Mechanical Engineering'), ('Medical Engineering', 'Medical Engineering'), ('Other', 'Other')], default="Computer Science")
	cellPhone = StringField('Cell Phone')
	email = StringField('Email', validators=[DataRequired(), Email()])
	profilePic = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
	submit = SubmitField('Apply')

	def validate_studentId(self, studentId):
		if not studentId.data.isdigit():
			raise ValidationError('Must contain only numbers!')

	def validate_firstNameHeb(self, firstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in firstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_lastNameHeb(self, lastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in lastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_firstNameEng(self, firstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in firstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_lastNameEng(self, lastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in lastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')
	
	def validate_cellPhone(self, cellPhone):
		if any(c.isalpha() for c in cellPhone.data):
			raise ValidationError('Not a valid cell phone number!')


class addProposedProjectForm(FlaskForm):
	newTitle = StringField('Title', validators=[DataRequired()])
	newDescription = TextAreaField('Description', validators=[DataRequired()])
	newImage = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
	newSupervisor1 = SelectField('Supervisor 1')
	newSupervisor2 = SelectField('Supervisor 2')
	newSupervisor3 = SelectField('Supervisor 3')
	submitAddForm = SubmitField('Add')

	def validate_newTitle(self, newTitle):
		titleExists = ProposedProject.query.filter_by(title=newTitle.data).first()
		if titleExists:
			raise ValidationError('There is already a proposed project with the same title')

class editProposedProjectForm(FlaskForm):
	proposedProjectId = HiddenField("")
	title = StringField('Title', validators=[DataRequired()])
	description = TextAreaField('Description', validators=[DataRequired()])
	image = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
	supervisor1 = SelectField('Supervisor 1')
	supervisor2 = SelectField('Supervisor 2')
	supervisor3 = SelectField('Supervisor 3')
	submitEditForm = SubmitField('Apply')

	def validate_title(self, title):
		currentProposedProject = ProposedProject.query.filter_by(id=self.proposedProjectId.data).first()
		# title was changed
		if self.title.data != currentProposedProject.title:
			titleExists = ProposedProject.query.filter_by(title=self.title.data).first()
			if titleExists:
				raise ValidationError('There is already a proposed project with the same title')

class deleteProposedProjectForm(FlaskForm):
	deleteProposedProjectId = HiddenField("")

class addProjectForm(FlaskForm):
	new_title = SelectField('Title')
	new_year = SelectField('Year')
	new_semester = SelectField('Semester')
	new_supervisor1 = SelectField('Supervisor 1')
	new_supervisor2 = SelectField('Supervisor 2')
	new_supervisor3 = SelectField('Supervisor 3')
	new_comments = TextAreaField('Comments')
	new_grade = StringField('Grade')
	new_requirementsDoc = BooleanField('מסמך דרישות')
	new_firstMeeting = BooleanField('פגישת התנעה')
	new_halfwayPresentation = BooleanField('מצגת אמצע')
	new_finalMeeting = BooleanField('פגישת סיום')
	new_projectReport = BooleanField('דו"ח פרוייקט')
	new_equipmentReturned = BooleanField('החזרת ציוד')
	new_projectDoc = BooleanField('דף פרוייקט')
	new_gradeStatus = BooleanField('ציון')

	submitAddForm = SubmitField('Create')

class editProjectForm(FlaskForm):
	projectId = HiddenField("")
	title = StringField('Title', validators=[DataRequired()])
	year = SelectField('Year')
	semester = SelectField('Semester')
	supervisor1 = SelectField('Supervisor 1')
	supervisor2 = SelectField('Supervisor 2')
	supervisor3 = SelectField('Supervisor 3')
	comments = TextAreaField('Comments')
	image = FileField('Project Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
	grade = StringField('Grade')
	requirementsDoc = BooleanField('מסמך דרישות')
	firstMeeting = BooleanField('פגישת התנעה')
	halfwayPresentation = BooleanField('מצגת אמצע')
	finalMeeting = BooleanField('פגישת סיום')
	projectReport = BooleanField('דו"ח פרוייקט')
	equipmentReturned = BooleanField('החזרת ציוד')
	projectDoc = BooleanField('דף פרוייקט')
	gradeStatus = BooleanField('ציון')

	submitEditForm = SubmitField('Apply')

class deleteProjectForm(FlaskForm):
	deleteProjectId = HiddenField("")

class deleteStudentForm(FlaskForm):
	deleteStudentId = HiddenField("")

class deleteSupervisorForm(FlaskForm):
	deleteSupervisorId = HiddenField("")

class editStudentForm(FlaskForm):
	id = HiddenField("")
	studentId = StringField('ID', validators=[DataRequired()])
	firstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	lastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	firstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	lastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	submitEditForm = SubmitField('Apply')

	def validate_studentId(self, studentId):
		if not studentId.data.isdigit():
			raise ValidationError('Must contain only numbers!')
		student = Student.query.filter_by(id=self.id.data).first()
		# is the id is in the db?
		if student: 
			# studentId changed?
			if self.studentId.data != student.studentId:
				studentWithNewIdExists =  Student.query.filter_by(studentId=self.studentId.data).first()
				if studentWithNewIdExists:
					raise ValidationError('There is already a student with the ID you entered')
	
	def validate_firstNameHeb(self, firstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in firstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_lastNameHeb(self, lastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in lastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_firstNameEng(self, firstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in firstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_lastNameEng(self, lastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in lastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')
	
	def validate_email(self, email):
		student = Student.query.filter_by(id=self.id.data).first()
		# is the id is in the db?
		if student:
			# email changed?
			if email.data != student.email:
				studentWithSameEmail =  Student.query.filter_by(email=email.data).first()
				if studentWithSameEmail:
					raise ValidationError('This email is already used by another student!')

class editSupervisorForm(FlaskForm):
	id = HiddenField("")
	supervisorId = StringField('ID', validators=[DataRequired()])
	firstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	lastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	firstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	lastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])
	email = StringField('Email')
	phone = StringField('Phone')
	status = SelectField('Stauts', choices=[('active', 'Active'), ('not active', 'Not Active')], validators=[DataRequired()])

	submitEditForm = SubmitField('Apply')

	def validate_firstNameHeb(self, firstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in firstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_lastNameHeb(self, lastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in lastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_firstNameEng(self, firstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in firstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_lastNameEng(self, lastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in lastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_supervisorId(self, supervisorId):
		if not supervisorId.data.isdigit():
				raise ValidationError('Must contain only numbers!')
		supervisor = Supervisor.query.filter_by(id=self.id.data).first()
		# is the id is in the db?
		if supervisor: 
			# supervisorId was changed
			if self.supervisorId.data != supervisor.supervisorId:
				supervisorWithNewIdExists =  Supervisor.query.filter_by(supervisorId=self.supervisorId.data).first()
				if supervisorWithNewIdExists:
					raise ValidationError('There is already a supervisor with the ID you entered')

class addSupervisorForm(FlaskForm):
	newSupervisorId = StringField('ID', validators=[DataRequired()])
	newFirstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	newLastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	newFirstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	newLastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])
	newEmail = StringField('Email', validators=[Optional(), Email()])
	newPhone = StringField('Phone')
	newStatus = SelectField('Stauts', choices=[('active', 'Active'), ('not active', 'Not Active')], validators=[DataRequired()])

	submitAddForm = SubmitField('Add')


	def validate_newFirstNameHeb(self, newFirstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in newFirstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_newLastNameHeb(self, newLastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in newLastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_newFirstNameEng(self, newFirstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in newFirstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_newLastNameEng(self, newLastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in newLastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_newSupervisorId(self, newSupervisorId):
		if not newSupervisorId.data.isdigit():
			raise ValidationError('Must contain only numbers!')
		supervisorExists = Supervisor.query.filter_by(supervisorId=self.newSupervisorId.data).first()
		if supervisorExists:
			raise ValidationError('There is already a supervisor with the ID you entered')

class joinAProjectForm(FlaskForm):
	projectTitle = SelectField('Project Title', validators=[DataRequired()])
	submitForm = SubmitField('Join')

class requestResetForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"placeholder": "Email"})
	submitForm = SubmitField('Send')

	def validate_email(self, email):
		student = Student.query.filter_by(email=email.data).first()
		if student is None:
			raise ValidationError('There is no account with that email.')

class resetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired(), Length(min=8)], render_kw={"placeholder": "New Password"})
	confirmPassword = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"placeholder": "Confirm New Password"})
	submitForm = SubmitField('Reset Password')
