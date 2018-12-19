from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from avr import db, login_manager, ma, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(userId):
	return User.query.get(userId)

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	userId = db.Column(db.String(20), unique=True, nullable=False)
	userType = db.Column(db.String(20), nullable=False)

	def __repr__(self):
		return "ProposedProject({}, {}, {})".format(self.id, self.userId, self.userType)

class StudentSchema(ma.Schema):
	class Meta:
		fields = ('id', 'studentId', 'firstNameEng', 'lastNameEng', 'firstNameHeb', 'lastNameHeb', 'faculty', 'cellPhone', 'email', 'semester', 'year', 'profilePic') 

class ProjectSchema(ma.Schema):
	class Meta:
		fields = ('id', 'title', 'semester', 'year', 'grade', 'comments', 'image', 'requirementsDoc', 'firstMeeting', 'halfwayPresentation', 'finalMeeting', 'projectReport', 'equipmentReturned', 'projectDoc', 'gradeStatus', 'studentsNamesHeb', 'studentsIds', 'studentsCourseIds', 'supervisorsIds')

class SupervisorSchema(ma.Schema):
	class Meta:
		fields = ('id', 'firstNameEng', 'lastNameEng')

class Student(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	studentId = db.Column(db.String(20), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)

	firstNameHeb = db.Column(db.String(30), nullable=False)
	lastNameHeb = db.Column(db.String(30), nullable=False)
	firstNameEng =  db.Column(db.String(30), nullable=False)
	lastNameEng = db.Column(db.String(30), nullable=False)

	academicStatus = db.Column(db.String(30), nullable=True)
	faculty = db.Column(db.String(30), nullable=False)
	cellPhone = db.Column(db.String(30), nullable=True)
	email = db.Column(db.String(150), nullable=False)
	semester = db.Column(db.String(20), nullable=False)
	year = db.Column(db.Integer, nullable=False)
	profilePic = db.Column(db.String(50), nullable=True)

	def get_reset_token(self, expires_sec=1800):
		s = Serializer(app.config['SECRET_KEY'], expires_sec)
		return s.dumps({'id': self.id}).decode('utf-8')
	
	@staticmethod
	def verify_reset_token(token):
		s = Serializer(app.config['SECRET_KEY'])
		try:
			id = s.loads(token)['id']
		except:
			return None
		return Student.query.get(id)

	@property
	def projectsSortedDesc(self):
		studentProjects = StudentProject.query.filter_by(studentId=self.id)
		projectsIds = [p.projectId for p in studentProjects]
		studentProjects = Project.query.filter(Project.id.in_(projectsIds)).all()
		projectsSortedDesc = sorted(studentProjects, key=lambda p: (-p.year, p.semester))
		return projectsSortedDesc

	def __repr__(self):
		return "Student({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.id, self.studentId, self.password, self.firstNameHeb, self.lastNameHeb, self.firstNameEng, self.lastNameEng, self.academicStatus, self.faculty, self.cellPhone, self.email, self.semester, self.year)


class ProposedProject(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(60), unique=True, nullable=False)
	description = db.Column(db.Text, nullable=False)
	image = db.Column(db.String(50), nullable=True)

	@property
	def supervisorsNames(self):
		supervisorProposedProject = SupervisorProposedProject.query.filter_by(proposedProjectId=self.id)
		supervisorsIds = [s.supervisorId for s in supervisorProposedProject]
		supervisors = []
		for supervisorId in supervisorsIds:
			supervisor = Supervisor.query.filter_by(id=supervisorId).first()
			supervisors.append(supervisor.firstNameEng + ' ' + supervisor.lastNameEng)
		return supervisors
	
	@property
	def supervisorsIds(self):
		supervisorProposedProject = SupervisorProposedProject.query.filter_by(proposedProjectId=self.id)
		supervisorsIds = [s.supervisorId for s in supervisorProposedProject]
		return supervisorsIds
	
	def __repr__(self):
		return "ProposedProject({}, {}, {}, {})".format(self.id, self.title, self.description, self.image)


class Project(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(60), nullable=False)
	semester = db.Column(db.String(20), nullable=False)
	year = db.Column(db.Integer, nullable=False)
	grade = db.Column(db.Integer, nullable=True)
	comments = db.Column(db.Text, nullable=True)
	image = db.Column(db.String(50), nullable=True)
	
	requirementsDoc = db.Column(db.Boolean, nullable=True, default=False)
	firstMeeting = db.Column(db.Boolean, nullable=True, default=False)
	halfwayPresentation = db.Column(db.Boolean, nullable=True, default=False)
	finalMeeting = db.Column(db.Boolean, nullable=True, default=False)
	projectReport = db.Column(db.Boolean, nullable=True, default=False)
	equipmentReturned = db.Column(db.Boolean, nullable=True, default=False)
	projectDoc = db.Column(db.Boolean, nullable=True, default=False)
	gradeStatus = db.Column(db.Boolean, nullable=True, default=False)
	
	def __repr__(self):
		return "Project({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.id, self.title, self.semester, self.year, self.grade, self.comments, self.requirementsDoc, self.firstMeeting, self.halfwayPresentation, self.finalMeeting, self.projectReport, self.equipmentReturned, self.projectDoc, self.gradeStatus)

	@property
	def supervisorsNames(self):
		supervisorsNames = []
		supervisorProject = SupervisorProject.query.filter_by(projectId=self.id)
		supervisorsIds = [s.supervisorId for s in supervisorProject]
		for supervisorId in supervisorsIds:
			supervisor = Supervisor.query.filter_by(id=supervisorId).first()
			supervisorsNames.append(supervisor.firstNameEng + " " + supervisor.lastNameEng)
		return supervisorsNames

	@property
	def supervisorsIds(self):
		supervisorProject = SupervisorProject.query.filter_by(projectId=self.id)
		supervisorsIds = [s.supervisorId for s in supervisorProject]
		return supervisorsIds

	@property
	def studentsNamesHeb(self):
		studentsNames = []
		studentsProjects = StudentProject.query.filter_by(projectId=self.id)
		studentsIds = [s.studentId for s in studentsProjects]
		for studentId in studentsIds:
			student = Student.query.filter_by(id=studentId).first()
			studentsNames.append(student.firstNameHeb+" "+student.lastNameHeb)
		return studentsNames
	
	@property
	def studentsNamesEng(self):
		studentsNames = []
		studentsProjects = StudentProject.query.filter_by(projectId=self.id)
		studentsIds = [s.studentId for s in studentsProjects]
		for studentId in studentsIds:
			student = Student.query.filter_by(id=studentId).first()
			studentsNames.append(student.firstNameEng+" "+student.lastNameEng)
		return studentsNames
	
	@property
	def studentsIds(self):
		studentsProjects = StudentProject.query.filter_by(projectId=self.id)
		studentsIds = [s.studentId for s in studentsProjects]
		return studentsIds

	@property
	def studentsCourseIds(self):
		studentsProjects = StudentProject.query.filter_by(projectId=self.id)
		courseIds = [s.courseId for s in studentsProjects]
		return courseIds
	
	@property
	def status(self):
		if self.gradeStatus:
			return "ציון"
		if self.projectDoc:
			return "דף פרוייקט"
		if self.projectReport:
			return 'דו"ח פרוייקט'
		if self.finalMeeting:
			return 'פגישת סיום'
		if self.halfwayPresentation:
			return "מצגת אמצע"
		if self.firstMeeting:
			return "פגישת התנעה"
		if self.requirementsDoc:
			return "מסמך דרישות"
		else:
			return "הרשמה"

		

class Supervisor(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	supervisorId = db.Column(db.String(20), unique=True, nullable=False)
	firstNameEng = db.Column(db.String(40), nullable=False)
	lastNameEng = db.Column(db.String(40),nullable=False)
	firstNameHeb = db.Column(db.String(40), nullable=False)
	lastNameHeb = db.Column(db.String(40),nullable=False)
	email = db.Column(db.String(150), nullable=True)
	phone = db.Column(db.String(20), nullable=True)
	status = db.Column(db.String(30), nullable=False, default="active")

	def __repr__(self):
		return "Supervisor({}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.id, self.supervisorId, self.firstNameEng, self.lastNameEng, self.firstNameHeb, self.lastNameHeb, self.email, self.phone, self.status)


# bridge table between supervisors and proposed projects
class SupervisorProposedProject(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	supervisorId = db.Column(db.Integer, db.ForeignKey('supervisor.id') ,nullable=False)
	proposedProjectId = db.Column(db.Integer, db.ForeignKey('proposed_project.id') ,nullable=False)

	def __repr__(self):
		return "SupervisorProposedProject({}, {}, {})".format(self.id, self.supervisorId, self.proposedProjectId)

# bridge table between supervisors and projects
class SupervisorProject(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	supervisorId = db.Column(db.Integer, db.ForeignKey('supervisor.id') ,nullable=False)
	projectId = db.Column(db.Integer, db.ForeignKey('project.id') ,nullable=False)

	def __repr__(self):
		return "SupervisorProject({}, {}, {})".format(self.id, self.supervisorId, self.projectId)


# bridge table between students and projects
class StudentProject(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	studentId = db.Column(db.Integer, db.ForeignKey('student.id') ,nullable=False)
	projectId = db.Column(db.Integer, db.ForeignKey('project.id') ,nullable=False)
	courseId = db.Column(db.Integer, db.ForeignKey('course.id') ,nullable=False)

	def __repr__(self):
		return "StudentProject({}, {}, {}, {})".format(self.id, self.studentId, self.projectId, self.courseId) 

class Admin(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	adminId = db.Column(db.String(20), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)

	def __repr__(self):
		return "Admin({}, {}, {})".format(self.id, self.adminId, self.password) 

class Course(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	number = db.Column(db.String(20), unique=True, nullable=False)
	name = db.Column(db.String(60), nullable=True)

	def __repr__(self):
		return "Course({}, {}, {})".format(self.id, self.number, self.name) 