import os
import json
from flask import render_template, url_for, flash, redirect, request, jsonify
from avr import app, db, bcrypt, mail
from avr.forms import (RegistrationForm, LoginForm, EditAccountForm, 
						addProposedProjectForm, editProposedProjectForm, 
						deleteProposedProjectForm, addProjectForm, editProjectForm, deleteProjectForm, editStudentForm, deleteStudentForm, editSupervisorForm, 
						deleteSupervisorForm, addSupervisorForm, joinAProjectForm, 
						requestResetForm, resetPasswordForm, createAdminForm)
from avr.models import (Student, User, Admin, Project, Supervisor, StudentProject,
						ProposedProject, Course)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from avr import utils
from avr import database
from avr.entities import courses, labs, proposedProjects, projects, students, supervisors, adminIndex
import traceback


@app.route('/logout', methods=['GET'])
def logout():
	logout_user()
	return redirect(url_for('login'))

################################
#          Admin URLS          #
################################


@app.route('/Admin', methods=['GET'])
def admin():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	return redirect(url_for('labOverview'))


@app.route('/Admin/Overview', methods=['GET'])
def labOverview():
	if not utils.check_user_lab_admin():
		return redirect(url_for('login'))

	admin = utils.check_user_admin()
	lab = None if not utils.check_user_lab() else database.getLabByAcronym(current_user.userId)
	overview = database.getLabOverview(lab)
	return render_template("/admin/labOverview.html", overview=overview, admin=admin, lab=lab)

@app.route('/Admin/sendMail', methods=['GET', 'POST'])
def adminMail(): return adminIndex.adminMail()

################################
#      Supervisors URLS        #
################################
@app.route('/Admin/Supervisors/Delete', methods=['POST'])
def deleteSupervisor(): return supervisors.deleteSupervisor()

@app.route('/Admin/Supervisors/<int:id>/json', methods=['GET', 'POST'])
def getSupervisorData(id): return supervisors.getSupervisorData(id)

@app.route('/Admin/Supervisors/json', methods=['GET', 'POST'])
def getSupervisorsTableData(): return supervisors.getSupervisorsTableData()

@app.route('/Admin/Supervisors', methods=['GET', 'POST'])
def manageSupervisors(): return supervisors.manageSupervisors()


################################
#        Students URLS         #
################################
@app.route('/Admin/Students/Delete', methods=['POST'])
def deleteStudent(): return students.deleteStudent()

@app.route('/Admin/Students/<int:id>/json', methods=['GET', 'POST'])
def getStudentData(id): return students.getStudentData(id)

@app.route('/Admin/StudentsForProject/json', methods=['GET', 'POST'])
def getStudentsTableForProjectData(): return students.getStudentsTableForProjectData()


@app.route('/Admin/Students/json', methods=['GET', 'POST'])
def getStudentsTableData(): return students.getStudentsTableData()

@app.route('/Admin/Students', methods=['GET', 'POST'])
def manageStudents(): return students.manageStudents()

@app.route('/register', methods=['GET', 'POST'])
def register(): return students.register()

@app.route('/EditAccount', methods=['GET', 'POST'])
def editAccount(): return students.editAccount()

################################
#       projects URLS          #
################################
@app.route('/Admin/Projects/<int:id>/json', methods=['GET', 'POST'])
def getProjectData(id): return projects.getProjectData(id)


@app.route('/Admin/Projects/Delete', methods=['POST'])
def deleteProject(): return projects.deleteProject()
	

@app.route('/Admin/Projects/json', methods=['GET', 'POST'])
def getProjectsTableData(): return projects.getProjectsTableData()

@app.route('/Admin/ProjectWithStudentsMail/json', methods=['GET', 'POST'])
def getProjectsTableDataWithMails(): return projects.getProjectsTableDataWithMails()


@app.route('/Admin/Projects', methods=['GET', 'POST'])
def manageProjects(): return projects.manageProjects()

@app.route('/ProjectStatus/<int:id>', methods=['GET'])
def projectStatus(id): return projects.projectStatus(id)

################################
#        courses URLS          #
################################
@app.route('/Admin/Courses', methods=['GET', 'POST'])
def manageCourses(): return courses.manageCourses()

@app.route('/Admin/Courses/json', methods=['GET', 'POST'])
def getCoursesTableData(): return courses.getCoursesTableData()


@app.route('/Admin/Courses/<int:id>/json', methods=['GET', 'POST'])
def getCourseData(id): return courses.getCourseData(id)

@app.route('/Admin/Courses/Delete', methods=['POST'])
def deleteCourse(): return courses.deleteCourse()


################################
#          labs URLS           #
################################
@app.route('/Admin/Labs', methods=['GET', 'POST'])
def manageLabs(): return labs.manageLabs()

@app.route('/Admin/Labs/json', methods=['GET', 'POST'])
def getLabsTableData(): return labs.getLabsTableData()


@app.route('/Admin/Labs/<int:id>/json', methods=['GET', 'POST'])
def getLabData(id): return labs.getLabData(id)

@app.route('/Admin/Labs/Delete', methods=['POST'])
def deleteLab(): return labs.deleteLab()

@app.route('/EditLab', methods=['GET', 'POST'])
def editLab(): return labs.editLab()



################################
#    ProposedProjects URLS     #
################################
@app.route('/ProposedProjects', methods=['GET','POST'])
def showProposedProjects(): return proposedProjects.showProposedProjects()


@app.route('/Admin/ProposedProjects/json', methods=['GET', 'POST'])
def getProposedProjectsTableData(): return proposedProjects.getProposedProjectsTableData()

@app.route('/Admin/ProposedProjects/Delete', methods=['POST'])
def deleteProposedProjects(): return proposedProjects.deleteProposedProjects()

@app.route('/Admin/ProposedProjects/<int:id>/json', methods=['GET', 'POST'])
def getProposedProjectData(id): return proposedProjects.getProposedProjectData(id)

@app.route('/Admin/ProposedProjects', methods=['GET', 'POST'])
def manageProposedProjects(): return proposedProjects.manageProposedProjects()


@app.route('/', methods=['GET'])
def index():
	try:
		# proposedProjects = database.getLimitedProposedProjects(5)
		labs = database.getAllLabs()
		student = None
		admin = None
		lab = None
		if current_user.is_authenticated:
			if current_user.userType == "student":
				student = database.getStudentByStudentId(current_user.userId)
			elif current_user.userType == "admin":
				admin = database.getAdminByAdminId(current_user.userId)
			elif current_user.userType == "lab":
				lab = database.getLabByAcronym(current_user.userId)
		return render_template('index.html', labs=labs, student=student, admin=admin, lab=lab)
		# return render_template('index.html', proposedProjects=proposedProjects, student=student, admin=admin)
	except Exception as e:
		app.logger.error('In index page, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/home', methods=['GET'])
def home():
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('labOverview'))
	if current_user.userType == "lab":
		return redirect(url_for('labOverview'))
	# user is a student
	try:
		student = database.getStudentByStudentId(current_user.userId)
		projects = student.projects
		return render_template('studentHome.html', title="Home", student=student, projects=projects)
	except Exception as e:
		app.logger.error('In home, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


def sendResetEmail(student):
	token = student.get_reset_token() 
	recipients=[student.email]
	msg = Message('Password Reset Request', sender='noreply@technion.ac.il', recipients=recipients)
	resetLink = url_for('resetToken', token=token, _external=True)
	msg.html = f'''To reset your password, visit the following link:<br>
	<a href="{resetLink}">{resetLink}</a>'''
	try:
		mail.send(msg)
		return True
	except Exception as e:
		flash('Error: could not send mail', 'danger')
		app.logger.error('In sendResetEmail, could not send mail to {}. Error is: {}\n{}'.format(recipients, e, traceback.format_exc()))
		return False

 
@app.route('/ResetPassword', methods=['GET', 'POST'])
def resetRequest():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		form = requestResetForm()
		if request.method == "POST":
			if form.validate_on_submit():
				student = database.getStudentByEmail(form.email.data)
				app.logger.info('In resetRequest, sending password reset email to {}'.format(student))
				emailWasSent = sendResetEmail(student)
				if emailWasSent:
					app.logger.info('In resetRequest, email was sent successfully to {}'.format(student))
					flash('An email has been sent with instructions to reset your password.', 'info')
					return redirect(url_for('login'))
			else:
				app.logger.info('In resetRequest, form is NOT valid. form.errors:{}'.format(form.errors))
				flash('There was an error, see details below.', 'danger')
		return render_template('resetRequest.html', title="Reset Password", form=form)
	except Exception as e:
		app.logger.error('In resetRequest, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/ResetPassword/<token>', methods=['GET', 'POST'])
def resetToken(token):
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		student = Student.verify_reset_token(token)
		if student is None:
			app.logger.info('In resetToken, token was invalid for {}'.format(student))
			flash('Invalid or expired token!', 'danger')
			return redirect(url_for('resetRequest'))
		form = resetPasswordForm()
		if request.method == "POST":
			if form.validate_on_submit():
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				app.logger.info('In resetToken, commiting new password to DB for {}'.format(student))
				database.updateStudent(student.id, {
					"password": hashed_password
				})
				flash('Your password has been updated successfully!', 'success')
				return redirect(url_for('login'))
			else:
				app.logger.info('In resetToken, form is NOT valid. form.errors:{}'.format(form.errors))
				flash('There was an error, see details below.', 'danger')
		return render_template('resetToken.html', title="Reset Password", form=form)
	except Exception as e:
		app.logger.error('In resetToken, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))

@app.route('/CreateAdminAccount', methods=['GET', 'POST'])
def createAdminAccount():
	if current_user.is_authenticated:
		app.logger.info('is_authenticated')
		return redirect(url_for('home'))
	try:
		totalAdmins = database.getAdminsCount()
		# allow **only one** admin to register

		if totalAdmins > 0:
			app.logger.info('totalAdmins > 0')
			return redirect(url_for('home'))

		form = createAdminForm()
		if request.method == "POST":
			if form.validate_on_submit():
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				# create admin
				database.addAdmin({
					"adminId": form.id.data,
					"password": hashed_password
				})				
				flash('Admin account was created successfully!', 'success')
				return redirect(url_for('login'))
			else:
				app.logger.info('In Create Admin Account, form is NOT valid. form.errors:{}'.format(form.errors))
				flash('There was an error, see details below.', 'danger')
		return render_template('/admin/createAdminAccount.html', title="Create Admin Account", form=form)
	except Exception as e:
		app.logger.error('In createAdminAccount, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))

@app.route('/Error', methods=['GET'])
def errorPage():
	return render_template('error.html', title="Error")

@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		form = LoginForm()
		if request.method == "POST":
			if form.validate_on_submit():
				userToLogIn = database.getUserByUserId(form.id.data.strip())
				if userToLogIn:
					if userToLogIn.userType == "admin":
						user = database.getAdminByAdminId(userToLogIn.userId)
					elif userToLogIn.userType == "student":
						user = database.getStudentByStudentId(userToLogIn.userId)
					elif userToLogIn.userType == "lab":
						user = database.getLabByAcronym(userToLogIn.userId)
					else:
						flash('userType is not recognized for this user.', 'danger')
					if bcrypt.check_password_hash(user.password, form.password.data):
						login_user(userToLogIn)
						return redirect(url_for('home'))
					else:
						app.logger.info('In Login, {} login was unsuccessful, password incorrect'.format(user.id))
						flash('Login unsuccessful: password is incorrect.', 'danger')
				else:
					flash('Login unsuccessful: user not registered.', 'danger')
			else:
				app.logger.info('In Login, form is NOT valid. form.errors:{}'.format(form.errors))
				if 'csrf_token' in form.errors:
					flash('Error: csrf token expired, please re-enter your credentials.', 'danger')
				else:	
					flash('There was an error, see details below.', 'danger')
		return render_template('login.html', title="Login", form=form)
	except Exception as e:
		app.logger.error('In login, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


