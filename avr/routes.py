import os
from shutil import copyfile
import secrets
import datetime
from flask import render_template, url_for, flash, redirect, request, jsonify
from avr import app, db, bcrypt, mail
from avr.forms import (RegistrationForm, LoginForm, EditAccountForm, 
						addProposedProjectForm, editProposedProjectForm, 
						deleteProposedProjectForm, addProjectForm, editProjectForm, deleteProjectForm, editStudentForm, deleteStudentForm, editSupervisorForm, 
						deleteSupervisorForm, addSupervisorForm, joinAProjectForm, 
						requestResetForm, resetPasswordForm, createAdminForm)
from avr.models import (Student, User, Admin, Project, Supervisor, 
						SupervisorProject, SupervisorProposedProject, StudentProject, 
						ProposedProject, StudentSchema, ProjectSchema, SupervisorSchema, Course)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from sqlalchemy_utils import database_exists

if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
	db.create_all()

defaultCourse = Course.query.filter_by(number='707021').first()
defaultCourseId = ''
if defaultCourse:
	defaultCourseId = defaultCourse.id

@app.route('/logout', methods=['GET'])
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route('/Admin', methods=['GET'])
def admin():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	return redirect(url_for('manageProjects'))

@app.route('/Admin/Supervisors/Delete', methods=['POST'])
def deleteSupervisor():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteSupervisorForm()
		supervisor = Supervisor.query.filter_by(id=deleteForm.deleteSupervisorId.data).first()
		if supervisor:
			# remove all proposed projects that this supervisor is related to
			SupervisorProposedProject.query.filter_by(supervisorId=supervisor.id).delete()
			
			# if this supervisor has/had any projects, don't delete it, just make it "not active"
			supervisorProject = SupervisorProject.query.filter_by(supervisorId=supervisor.id).first()
			if supervisorProject:
				app.logger.info('In deleteSupervisor, changing supervisor {} status to not active'.format(supervisor))
				supervisor.status = "not active"
				flash('Supervisor has related projects, it was NOT deleted. Instead, it became not active.', 'info')
			else:
				app.logger.info('In deleteSupervisor, deleting supervisor {}'.format(supervisor))
				db.session.delete(supervisor)
				flash('Supervisor was deleted successfully!', 'primary')
			db.session.commit()
		else:
			app.logger.info('In deleteSupervisor, could not delete supervisor with id {}, because there is no supervisor with this id'.format(deleteForm.deleteSupervisorId.data))
			flash("Error: can't delete, supervisor id is not in the db", 'danger')
		return redirect(url_for('manageSupervisors'))
	except Exception as e:
		app.logger.error('In deleteSupervisor, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))

@app.route('/Admin/Supervisors', methods=['GET', 'POST'])
def manageSupervisors():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		supervisors = Supervisor.query.all()
		addForm = addSupervisorForm()
		editForm = editSupervisorForm()
		deleteForm = deleteSupervisorForm()
		addFormErrors = False
		editFormErrorSupervisorId = ''
		if(request.method == 'POST'):
			formName = request.form['sentFormName']
			editForm.email.data = editForm.email.data.strip()
			addForm.newEmail.data = addForm.newEmail.data.strip()
			if formName == 'editForm':
				supervisor = Supervisor.query.filter_by(id=editForm.id.data).first()
				if not supervisor:
					app.logger.error('In manageSupervisors, in editForm, tried to edit a supervisor with id {} that does not exist in the db'.format(editForm.id.data))
					flash("Error: supervisor with id {} is not in the db.".format(editForm.id.data), 'danger')
					return redirect(url_for('manageSupervisors'))
				if editForm.validate_on_submit():
					supervisor.supervisorId = editForm.supervisorId.data
					supervisor.firstNameEng = editForm.firstNameEng.data
					supervisor.lastNameEng = editForm.lastNameEng.data
					supervisor.firstNameHeb = editForm.firstNameHeb.data
					supervisor.lastNameHeb = editForm.lastNameHeb.data
					supervisor.email = editForm.email.data
					supervisor.phone = editForm.phone.data
					supervisor.status = editForm.status.data
					app.logger.info('In manageSupervisors, in editForm, commiting supervisor {} changes'.format(supervisor))
					db.session.commit()
					flash('Supervisor was updated successfully!', 'success')
					return redirect(url_for('manageSupervisors'))
				else:
					app.logger.info('In manageSupervisors, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					editFormErrorSupervisorId = editForm.id.data
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')
			if formName == 'addForm':
				if addForm.validate_on_submit():
					newSupervisor = Supervisor(supervisorId=addForm.newSupervisorId.data, firstNameEng=addForm.newFirstNameEng.data.capitalize(), lastNameEng=addForm.newLastNameEng.data.capitalize(), firstNameHeb=addForm.newFirstNameHeb.data, lastNameHeb=addForm.newLastNameHeb.data, email=addForm.newEmail.data, phone=addForm.newPhone.data, status=addForm.newStatus.data)
					app.logger.info('In manageSupervisors, in addForm, adding new supervisor {} to DB'.format(newSupervisor))
					db.session.add(newSupervisor)
					db.session.commit()

					flash('Supervisor created successfully!', 'success')
					return redirect(url_for('manageSupervisors'))
				else:
					app.logger.info('In manageSupervisors, addForm is NOT valid. addForm.errors: {}'.format(addForm.errors))
					addFormErrors = True
					if 'csrf_token' in addForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')
		return render_template('/admin/supervisors.html', title="Manage Supervisors", editForm=editForm, deleteForm=deleteForm, addForm=addForm, editFormErrorSupervisorId=editFormErrorSupervisorId, addFormErrors=addFormErrors, supervisors=supervisors)
	except Exception as e:
		app.logger.error('In manageSupervisors, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))

@app.route('/Admin/Students/<int:year>/<string:semester>', methods=['POST', 'GET'])
def getAllStudentsInYearSemester(year, semester):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		students = Student.query.filter_by(year=year, semester=semester).all()
		studentsSchema = StudentSchema(many=True)
		result = studentsSchema.dump(students)
		return jsonify(result.data)
	except Exception as e:
		app.logger.error('In getAllStudentsInYearSemester with year: {}, semester: {}, Error is: {}'.format(year, semester, e))
		return "[]"

@app.route('/Admin/Students/Delete', methods=['POST'])
def deleteStudent():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteStudentForm()
		student = Student.query.filter_by(id=deleteForm.deleteStudentId.data).first()
		if student:
			# remove all projects that this student is related to
			StudentProject.query.filter_by(studentId=deleteForm.deleteStudentId.data).delete()
			# remove from user table
			studentUser = User.query.filter_by(userId=student.studentId).first()		
			app.logger.info('In deleteStudent, deleting user {}'.format(studentUser))
			db.session.delete(studentUser)

			# delete profile pic if exists
			picFile = student.profilePic
			if picFile:
				picFolder = os.path.join(app.root_path, 'static', 'images', 'profile')
				try:
					os.remove(os.path.join(picFolder, picFile))
				except OSError as e:
					app.logger.error('In deleteStudent, could not delete image {}, Error is: {}'.format(os.path.join(picFolder, picFile), e))

			app.logger.info('In deleteStudent, deleting student {}'.format(student))
			db.session.delete(student)
			db.session.commit()
			flash('Student was deleted successfully!', 'success')
		else:
			app.logger.info('In deleteStudent, could not delete student with id {}, because there is no student with this id'.format(deleteForm.deleteStudentId.data))
			flash("Error: can't delete, student id is not in the db", 'danger')
		return redirect(url_for('manageStudents'))
	except Exception as e:
		app.logger.error('In deleteStudent, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))


@app.route('/Admin/Students/<int:id>/LastProjects/', methods=['GET', 'POST'])
def getStudentLastProjects(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		student = Student.query.get(id)
		projects = [project for project in student.projectsSortedDesc]
		projectSchema = ProjectSchema(many=True)
		result = projectSchema.dump(projects)
		return jsonify(result.data)
	except Exception as e:
		app.logger.error('In getStudentLastProjects with id: {}, Error is: {}'.format(id, e))
		return "[]"


@app.route('/Admin/Students/<int:id>/json', methods=['GET', 'POST'])
def getStudentData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		student = Student.query.filter_by(id=id)
		studentSchema = StudentSchema(many=True)
		result = studentSchema.dump(student)
		return jsonify(result.data)
	except Exception as e:
		app.logger.error('In getStudentData with id: {}, Error is: {}'.format(id, e))
		return "[]"


@app.route('/Admin/Students/<int:id>', methods=['GET'])
@app.route('/Admin/Students', defaults={'id': None}, methods=['GET', 'POST'])
def manageStudents(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		students = Student.query.all()
		editForm = editStudentForm()
		edit_ProjectForm = editProjectForm()
		courses = Course.query.all()
		deleteForm = deleteStudentForm()
		editFormErrorStudentId = ''
		editProjectErrorId = ''
		currentSemester = getRegistrationSemester()
		currentYear = getRegistrationYear()
		semesterChoices = []
		if currentSemester == "Winter":
			semesterChoices = [("Winter", "Winter"), ("Spring", "Spring")]
		else:
			semesterChoices = [("Spring", "Spring"), ("Winter", "Winter")]

		allSupervisors = Supervisor.query.all()
		supervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in allSupervisors]
		supervisorsChoices.insert(0, ('', ''))

		edit_ProjectForm.year.choices = [(currentYear, currentYear), (str(int(currentYear)+1),str(int(currentYear)+1)), (str(int(currentYear)+2),str(int(currentYear)+2))]
		edit_ProjectForm.semester.choices = semesterChoices
		edit_ProjectForm.supervisor1.choices = supervisorsChoices
		edit_ProjectForm.supervisor2.choices = supervisorsChoices
		edit_ProjectForm.supervisor3.choices = supervisorsChoices

		
		if id:
			# is the id valid?
			student = Student.query.filter_by(id=id).first()
			if student:
				editFormErrorStudentId = id
			else:
				app.logger.info('In manageStudents, tried to access /Admin/Students/<id> with id: {}. there is no student with this id'.format(id))
				flash('Error: student with id {} does not exist!'.format(id), 'danger')

		if(request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editForm':
				student = Student.query.filter_by(id=editForm.id.data).first()
				if not student:
					app.logger.error('In manageStudents, in editForm, tried to edit a student with id {} that does not exist in the db'.format(editForm.id.data))
					flash("Error: student with id {} is not in the db.".format(editForm.id.data), 'danger')
					return redirect(url_for('manageStudents'))
				if editForm.validate_on_submit():
					student.studentId = editForm.studentId.data
					student.firstNameEng = editForm.firstNameEng.data.capitalize()
					student.lastNameEng = editForm.lastNameEng.data.capitalize()
					student.firstNameHeb = editForm.firstNameHeb.data
					student.lastNameHeb = editForm.lastNameHeb.data
					student.email = editForm.email.data
					app.logger.info('In manageStudents, commiting student {} changes'.format(student))
					db.session.commit()
					flash('Student was updated successfully!', 'success')
					return redirect(url_for('manageStudents'))
				else:
					app.logger.info('In manageStudents, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					editFormErrorStudentId = editForm.id.data
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')

		return render_template('/admin/students.html', title="Manage Students", editForm=editForm, editProjectForm=edit_ProjectForm, courses=courses, defaultCourseId=defaultCourseId, deleteForm=deleteForm, editFormErrorStudentId=editFormErrorStudentId, students=students)
	except Exception as e:
		app.logger.error('In manageStudents, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))


@app.route('/Admin/Projects/<int:id>/json', methods=['GET', 'POST'])
def getProjectData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try: 
		project = Project.query.filter_by(id=id)
		projectSchema = ProjectSchema(many=True)
		result = projectSchema.dump(project)
		return jsonify(result.data)
	except Exception as e:
		app.logger.error('In getProjectData with id: {}, Error is: {}'.format(id, e))
		return "{}"

@app.route('/Admin/Projects/Delete', methods=['POST'])
def deleteProject():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteProjectForm()
		project = Project.query.filter_by(id=deleteForm.deleteProjectId.data).first()
		if project:
			picFile = project.image
			# delete project image if exists
			if picFile is not None:
				picFolder = os.path.join(app.root_path, 'static', 'images', 'projects')
				try:
					os.remove(os.path.join(picFolder, picFile))
				except OSError as e:
					app.logger.error('In deleteProjects, could not delete image {}, Error is: {}'.format(os.path.join(picFolder, picFile), e))
			
			# delete all students from project
			StudentProject.query.filter_by(projectId=project.id).delete()
			# delete all supervisors from project
			SupervisorProject.query.filter_by(projectId=project.id).delete()
			# delete project
			app.logger.info('In deleteProject, deleting {}'.format(project))
			db.session.delete(project)
			db.session.commit()
			flash('Project was deleted successfully!', 'primary')
		else:
			app.logger.error('In deleteProject, could not delete project with id {}, because there is no project with this id'.format(deleteForm.deleteProjectId.data))
			flash("Error: can't delete, project id {} is not in the db".format(deleteForm.deleteProjectId.data), 'danger')
		return redirect(url_for('manageProjects'))
	except Exception as e:
		app.logger.error('In deleteProject, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))
	

@app.route('/Admin/Projects/<int:id>', methods=['GET'])
@app.route('/Admin/Projects', defaults={'id': None}, methods=['GET', 'POST'])
def manageProjects(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		projects = Project.query.all()
		students = Student.query.all()
		courses = Course.query.all()
		addForm = addProjectForm()
		editForm = editProjectForm()
		deleteForm = deleteProjectForm()
		addFormErrors = False
		editFormErrorProjectId = ''
		edit_studentForm = editStudentForm()
		
		currentSemester = getRegistrationSemester()
		currentYear = getRegistrationYear()
		semesterChoices = []
		if currentSemester == "Winter":
			semesterChoices = [("Winter", "Winter"), ("Spring", "Spring")]
		else:
			semesterChoices = [("Spring", "Spring"), ("Winter", "Winter")]
		addForm.new_title.choices = [(str(s.id), s.title) for s in ProposedProject.query.all()]
		addForm.new_year.choices = [(currentYear, currentYear), (str(int(currentYear)+1),str(int(currentYear)+1)), (str(int(currentYear)+2),str(int(currentYear)+2))]
		addForm.new_semester.choices = semesterChoices

		allSupervisors = Supervisor.query.all()
		supervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in allSupervisors]
		supervisorsChoices.insert(0, ('', ''))
		addForm.new_supervisor1.choices = supervisorsChoices
		addForm.new_supervisor2.choices = supervisorsChoices
		addForm.new_supervisor3.choices = supervisorsChoices

		editForm.year.choices = [(currentYear, currentYear), (str(int(currentYear)+1),str(int(currentYear)+1)), (str(int(currentYear)+2),str(int(currentYear)+2))]
		editForm.semester.choices = semesterChoices
		editForm.supervisor1.choices = supervisorsChoices
		editForm.supervisor2.choices = supervisorsChoices
		editForm.supervisor3.choices = supervisorsChoices

		if id:
			# is the id valid?
			project = Project.query.filter_by(id=id).first()
			if project:
				editFormErrorProjectId = id
			else:
				app.logger.info('In manageProjects, tried to access /Admin/Projects/<id> with id: {}. there is no project with this id'.format(id))
				flash('Error: project with id {} does not exist!'.format(id), 'danger')
		if(request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editForm':
				project = Project.query.filter_by(id=editForm.projectId.data).first()

				if not project:
					app.logger.error('In manageProjects, in editForm, tried to edit a project with id {} that does not exist in the db'.format(editForm.projectId.data))
					flash("Error: project with id {} is not in the db.".format(editForm.projectId.data), 'danger')
					return redirect(url_for('manageProjects'))

				if editForm.validate_on_submit():
					projectHadGrade = project.grade
					project.title = editForm.title.data	
					project.year = editForm.year.data			
					project.semester = editForm.semester.data			
					project.comments = editForm.comments.data
					project.grade = editForm.grade.data
					
					picFile = project.image
					if editForm.image.data:
						# delete old image if exists
						app.logger.info('In manageProjects, in editForm, deleting old project image')
						if picFile is not None:
							picFolder = os.path.join(app.root_path, 'static', 'images', 'projects')
							try:
								os.remove(os.path.join(picFolder, picFile))
							except OSError as e:
								app.logger.error('In manageProjects, could not delete old project image {}, Error is: {}'.format(os.path.join(picFolder, picFile), e))
						picFile = save_image(editForm.image.data, "projects")
						app.logger.info('In manageProjects, in editForm, new image {} was saved successfully'.format(picFile))
					project.image = picFile

					# update students in project
					studentsIds = request.form.getlist("students")
					studentsCoursesIds = request.form.getlist("studentsCoursesIds")
					# ---- delete current students
					StudentProject.query.filter_by(projectId=project.id).delete()
					# ---- add new students to projects
					for i in range(len(studentsIds)):
						studentProject = StudentProject(projectId=project.id, studentId=studentsIds[i], courseId=studentsCoursesIds[i])
						app.logger.info('In manageProjects, in editForm, adding new studentProject: {}'.format(studentProject))
						db.session.add(studentProject)
						# register students
						Student.query.filter_by(id=studentsIds[i]).first().isRegistered = True
					
					# ---------------- update supervisors in project -------------------
					# delete all current supervisors
					supervisorProject = SupervisorProject.query.filter_by(projectId=project.id).delete()
					# add new ones
					supervisorsIds = set()
					if editForm.supervisor1.data:
						supervisorsIds.add(editForm.supervisor1.data)
					if editForm.supervisor2.data:
						supervisorsIds.add(editForm.supervisor2.data)
					if editForm.supervisor3.data:
						supervisorsIds.add(editForm.supervisor3.data)
					for supervisorId in supervisorsIds:
						supervisorProject = SupervisorProject(supervisorId=supervisorId, projectId=project.id)
						app.logger.info('In manageProjects, in editForm, adding new supervisorProject: {}'.format(supervisorProject))
						db.session.add(supervisorProject)

					# update status
					project.requirementsDoc = editForm.requirementsDoc.data
					project.firstMeeting = editForm.firstMeeting.data
					project.halfwayPresentation = editForm.halfwayPresentation.data
					project.finalMeeting = editForm.finalMeeting.data
					project.projectReport = editForm.projectReport.data
					project.equipmentReturned = editForm.equipmentReturned.data
					project.projectDoc = editForm.projectDoc.data
					project.gradeStatus = editForm.gradeStatus.data

					app.logger.info('In manageProjects, in editForm, commiting project {} changes'.format(project))
					db.session.commit()
					
					flash('Project was updated successfully!', 'success')
					if request.form.get('studentsReferrer'):
						return redirect(url_for('manageStudents'))
					else:
						return redirect(url_for('manageProjects'))
				else:
					app.logger.info('In manageProjects, editForm is NOT valid. editForm.errors:{}'.format(editForm.errors))
					editFormErrorProjectId = editForm.projectId.data
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')
					if request.form.get('studentsReferrer'):
						edit_StudentForm = editStudentForm()
						delete_StudentForm = deleteStudentForm()
						editFormErrorStudentId = ''

						return render_template('/admin/students.html', title="Manage Students", editForm=edit_StudentForm, editProjectForm=editForm, courses=courses, defaultCourseId=defaultCourseId, deleteForm=delete_StudentForm, editFormErrorStudentId=editFormErrorStudentId, editProjectErrorId=editFormErrorProjectId, students=students)


			elif formName == 'addForm':
				if addForm.validate_on_submit():				
					# add new project
					new_projectTitle = dict(addForm.new_title.choices).get(addForm.new_title.data)
					newImageName = None
					# save project image
					matchingProposedProject = ProposedProject.query.filter_by(title=new_projectTitle).first()
					if matchingProposedProject:
						matchingImageName = matchingProposedProject.image
						if matchingImageName:
							random_hex = secrets.token_hex(8)
							_, matchingExt = os.path.splitext(matchingImageName)
							newImageName = random_hex + matchingExt
							sourcePath = os.path.join(app.root_path, 'static', 'images', 'proposed_projects', matchingImageName)
							app.logger.info('In manageProjects, in addForm, saving image of project to {}'.format(os.path.join(app.root_path, 'static', 'images', 'projects', newImageName)))
							copy_image(sourcePath, os.path.join(app.root_path, 'static', 'images', 'projects'), newImageName)

					newProject = Project(title=new_projectTitle, year=addForm.new_year.data, semester=addForm.new_semester.data, grade=addForm.new_grade.data, comments=addForm.new_comments.data, image=newImageName,requirementsDoc=addForm.new_requirementsDoc.data, firstMeeting=addForm.new_firstMeeting.data, halfwayPresentation=addForm.new_halfwayPresentation.data, finalMeeting=addForm.new_finalMeeting.data, projectReport=addForm.new_projectReport.data, equipmentReturned=addForm.new_equipmentReturned.data, projectDoc=addForm.new_projectDoc.data, gradeStatus=addForm.new_gradeStatus.data)
					db.session.add(newProject)
					app.logger.info('In manageProjects, in addForm, adding new project {} to db'.format(newProject))
					db.session.commit()

					# add students to project
					studentsIds = request.form.getlist("students")
					studentsCoursesIds = request.form.getlist("studentsCoursesIds")
					for i in range(len(studentsIds)):
						studentProject = StudentProject(projectId=newProject.id, studentId=studentsIds[i], courseId=studentsCoursesIds[i])
						app.logger.info('In manageProjects, in addForm, adding new studentProject: {}'.format(studentProject))
						db.session.add(studentProject)
						# register students
						Student.query.filter_by(id=studentsIds[i]).first().isRegistered = True

					# add supervisors to project
					supervisorsIds = set()
					if addForm.new_supervisor1.data:
						supervisorsIds.add(addForm.new_supervisor1.data)
					if addForm.new_supervisor2.data:
						supervisorsIds.add(addForm.new_supervisor2.data)
					if addForm.new_supervisor3.data:
						supervisorsIds.add(addForm.new_supervisor3.data)
					for supervisorId in supervisorsIds:
						supervisorProject = SupervisorProject(supervisorId=supervisorId, projectId=newProject.id)
						app.logger.info('In manageProjects, in addForm, adding new supervisorProject: {}'.format(supervisorProject))
						db.session.add(supervisorProject)

					db.session.commit()
					flash('Project was created successfully!', 'success')
					return redirect(url_for('manageProjects'))
				else:
					addFormErrors = True
					app.logger.info('In manageProjects, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
					if 'csrf_token' in addForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')
		return render_template('/admin/projects.html', title="Manage Projects", projects=projects, students=students, courses=courses, defaultCourseId=defaultCourseId, addForm=addForm, editForm=editForm, deleteForm=deleteForm, addFormErrors=addFormErrors, editFormErrorProjectId=editFormErrorProjectId, editStudentForm=edit_studentForm)
	except Exception as e:
		app.logger.error('In manageProjects, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))


@app.route('/Admin/ProposedProjects/Delete', methods=['POST'])
def deleteProposedProjects():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteProposedProjectForm()
		proposedProject = ProposedProject.query.filter_by(id=deleteForm.deleteProposedProjectId.data).first()
		if proposedProject:
			picFile = proposedProject.image
			# delete image if exists
			if picFile is not None:
				picFolder = os.path.join(app.root_path, 'static', 'images', 'proposed_projects')
				try:
					os.remove(os.path.join(picFolder, picFile))
				except OSError as e:
					app.logger.error('In deleteProposedProjects, could not delete image {}, Error is: {}'.format(os.path.join(picFolder, picFile), e))
			
			# remove all supervisors from this proposed project
			SupervisorProposedProject.query.filter_by(proposedProjectId=proposedProject.id).delete()
			app.logger.info('In deleteProposedProjects, deleting {}'.format(proposedProject))
			db.session.delete(proposedProject)
			db.session.commit()
			flash('Proposed Project was deleted successfully!', 'primary')
		else:
			app.logger.info('In deleteProposedProjects, could not delete proposed project with id {}, because there is no proposed project with this id'.format(deleteForm.deleteProposedProjectId.data))
			flash("Error: can't delete, proposed project id is not in the db", 'danger')
		return redirect(url_for('manageProposedProjects'))
	except Exception as e:
		app.logger.error('In deleteProposedProjects, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))
	

@app.route('/Admin/ProposedProjects', methods=['GET', 'POST'])
def manageProposedProjects():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		addForm = addProposedProjectForm()
		editForm = editProposedProjectForm()
		deleteForm = deleteProposedProjectForm()
		addFormErrors = False
		editFormErrorProposedProjectId = ''

		# get supervisors
		allSupervisors = Supervisor.query.filter_by(status="active")
		supervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in allSupervisors]
		supervisorsChoices.insert(0, ('', ''))

		editForm.supervisor1.choices = supervisorsChoices
		editForm.supervisor2.choices = supervisorsChoices
		editForm.supervisor3.choices = supervisorsChoices 

		addForm.newSupervisor1.choices = supervisorsChoices
		addForm.newSupervisor2.choices = supervisorsChoices
		addForm.newSupervisor3.choices = supervisorsChoices 
		
		if(request.method == 'POST'):
			formName = request.form['pageForm']
			if formName == 'addForm':
				if addForm.validate_on_submit():			
					app.logger.info('In manageProposedProjects, addForm was valid')
					picFile = None
					if addForm.newImage.data:
						app.logger.info('In manageProposedProjects, saving image of new proposed project')
						picFile = save_image(addForm.newImage.data, "proposed_projects")
					
					# create new proposed project
					newProposedProject = ProposedProject(title=addForm.newTitle.data, description=addForm.newDescription.data, image=picFile)
					app.logger.info('In manageProposedProjects, adding new proposed project: {}'.format(newProposedProject))
					db.session.add(newProposedProject)
					db.session.commit()
					
					# save the supervisors for this proposed project
					supervisorsIds = set()
					if addForm.newSupervisor1.data:
						supervisorsIds.add(int(addForm.newSupervisor1.data))
					if addForm.newSupervisor2.data:
						supervisorsIds.add(int(addForm.newSupervisor2.data))
					if addForm.newSupervisor3.data:
						supervisorsIds.add(int(addForm.newSupervisor3.data))
					for supervisorId in supervisorsIds:
						supervisorProposedProject = SupervisorProposedProject(supervisorId=supervisorId, proposedProjectId=newProposedProject.id)
						db.session.add(supervisorProposedProject)
					db.session.commit()
					
					flash('Proposed project created successfully!', 'success')
					return redirect(url_for('manageProposedProjects'))
				else:
					app.logger.info('In manageProposedProjects, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
					if 'csrf_token' in addForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:
						flash('There was an error, see details below.', 'danger')
					addFormErrors = True
			elif formName == 'editForm':
				proposedProject = ProposedProject.query.filter_by(id=editForm.proposedProjectId.data).first()

				if not proposedProject:
					app.logger.error('In manageProposedProjects, in editForm, tried to edit a proposed project with id {} that does not exist in the db'.format(editForm.proposedProjectId.data))
					flash("Error: project with id {} is not in the db.".format(editForm.proposedProjectId.data), 'danger')
					return redirect(url_for('manageProposedProjects'))

				if editForm.validate_on_submit():	
					picFile = proposedProject.image
					if editForm.image.data:
						# delete old image if exists
						app.logger.info('In manageProposedProjects, in editForm, deleting old image')
						if picFile is not None:
							picFolder = os.path.join(app.root_path, 'static', 'images', 'proposed_projects')
							try:
								os.remove(os.path.join(picFolder, picFile))
							except OSError as e:
								app.logger.error('In manageProposedProjects, could not delete old image {}, Error is: {}'.format(os.path.join(picFolder, picFile), e))
						picFile = save_image(editForm.image.data, "proposed_projects")
						app.logger.info('In manageProposedProjects, in editForm, new image {} was saved successfully'.format(picFile))
					
					proposedProject.title = editForm.title.data
					proposedProject.description = editForm.description.data
					proposedProject.image = picFile

					# update supervisors for this proposed project
					currentSupervisors = set(proposedProject.supervisorsIds)
					newSupervisors = set()
					if editForm.supervisor1.data:
						newSupervisors.add(int(editForm.supervisor1.data))
					if editForm.supervisor2.data:
						newSupervisors.add(int(editForm.supervisor2.data))
					if editForm.supervisor3.data:
						newSupervisors.add(int(editForm.supervisor3.data))
					supervisorsIdsToAdd = (newSupervisors - currentSupervisors)
					supervisorsIdsToRemove = (currentSupervisors - newSupervisors)
					for supervisorId in supervisorsIdsToRemove:
						SupervisorProposedProject.query.filter_by(proposedProjectId=proposedProject.id, supervisorId=supervisorId).delete()
					for supervisorId in supervisorsIdsToAdd:
						supervisorToAdd = SupervisorProposedProject(proposedProjectId=proposedProject.id, supervisorId=supervisorId)
						db.session.add(supervisorToAdd)

					app.logger.info('In manageProposedProjects, in editForm, commiting proposed project {} changes to DB'.format(proposedProject))
					db.session.commit()
					flash('Proposed project was updated successfully!', 'success')
					return redirect(url_for('manageProposedProjects'))
				else:
					app.logger.info('In manageProposedProjects, editForm is NOT valid. editForm.errors:{}'.format(editForm.errors))
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:
						flash('There was an error, see details below.', 'danger')
					editFormErrorProposedProjectId = editForm.proposedProjectId.data
		
		proposedProjects = ProposedProject.query.all()		
		return render_template('/admin/proposedProjects.html', title="Manage Proposed Projects", proposedProjects=proposedProjects, addForm=addForm, editForm=editForm, deleteForm=deleteForm, addFormErrors=addFormErrors, editFormErrorProposedProjectId=editFormErrorProposedProjectId)
	except Exception as e:
		app.logger.error('In manageProposedProjects, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))

@app.route('/ProjectStatus/<int:id>', methods=['GET'])
def projectStatus(id):
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('manageProjects'))
	# user is a student
	try:
		student = Student.query.filter_by(studentId=current_user.userId).first()
		project = None
		studentInProject = StudentProject.query.filter_by(projectId=id, studentId=student.id).first()
		if not studentInProject:
			flash("You are not enrolled in the project.", 'danger')
		else:
			project = Project.query.filter_by(id=id).first()

		return render_template('projectStatus.html', title="Project Status", student=student, project=project, studentInProject=studentInProject)
	except Exception as e:
		app.logger.error('In projectStatus, Error is: {}'.format(e))
		return redirect(url_for('errorPage'))


######################################################
# for now, students can't join projects
######################################################
# @app.route('/JoinAProject', methods=['GET', 'POST'])
def joinAProject():
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('manageProjects'))
	# user is a student
	student = Student.query.filter_by(studentId=current_user.userId).first()
	form = joinAProjectForm()
	projectTitleChoices = [(s.title, s.title) for s in ProposedProject.query.all()]
	projectTitleChoices.insert(0, ('', ''))
	form.projectTitle.choices = projectTitleChoices

	if request.method == "POST":
		if form.validate_on_submit():
			registrationSemester = getRegistrationSemester()
			registrationYear = getRegistrationYear()
			# is another student from the same project already registred?
			projectExists = Project.query.filter_by(year=registrationYear, semester=registrationSemester, title=form.projectTitle.data).first()
			if not projectExists:
				project = Project(title=form.projectTitle.data, semester=registrationSemester, year=registrationYear)
				db.session.add(project)
			else:
				# project does exist, is the student already registred with this project?
				studentRegistred = StudentProject.query.filter_by(studentId=student.id, projectId=projectExists.id).first()
				if studentRegistred:
					flash("You've already joined this project!", 'danger')
					return redirect(url_for('joinAProject'))		
			projectId = Project.query.filter_by(year=registrationYear, semester=registrationSemester, title=form.projectTitle.data).first().id
			# register the student in this project
			studentProject = StudentProject(studentId=student.id, projectId=projectId)
			db.session.add(studentProject)
			db.session.commit()	
			flash('You have joined the project successfully!', 'success')
			return redirect(url_for('home'))

		else:
			flash('There was an error, see details below.', 'danger')
	student = Student.query.filter_by(studentId=current_user.userId).first()
	return render_template('joinAProject.html', title="Join a Project", student=student, form=form)


@app.route('/', methods=['GET'])
def index():
	try:
		proposedProjects = ProposedProject.query.all()
		student = None
		admin = None
		if current_user.is_authenticated:
			if current_user.userType == "student":
				student = Student.query.filter_by(studentId=current_user.userId).first()
			elif current_user.userType == "admin":
				admin = Admin.query.filter_by(adminId=current_user.userId).first()
		return render_template('index.html', proposedProjects=proposedProjects, student=student, admin=admin)
	except Exception as e:
		app.logger.error('In index page, Error is: {}'.format(e))
		return redirect(url_for('errorPage'))

@app.route('/home', methods=['GET'])
def home():
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('manageProjects'))
	# user is a student
	try:
		student = Student.query.filter_by(studentId=current_user.userId).first()
		projectsIds = StudentProject.query.filter_by(studentId=student.id)
		projects = [Project.query.filter_by(id=p.projectId).first() for p in projectsIds]
		return render_template('studentHome.html', title="Home", student=student, projects=projects)
	except Exception as e:
		app.logger.error('In home, Error is: {}'.format(e))
		return redirect(url_for('errorPage'))

@app.route('/ProposedProjects', methods=['GET'])
def proposedProjects():
	try:
		proposedProjects = ProposedProject.query.all()
		return render_template('proposedProjects.html', title="Proposed Projects", proposedProjects=proposedProjects)
	except Exception as e:
		app.logger.error('In proposedProjects, Error is: {}'.format(e))
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
		app.logger.error('In sendResetEmail, could not send mail to {}. Error is: {}'.format(recipients, e))
		return False

 
@app.route('/ResetPassword', methods=['GET', 'POST'])
def resetRequest():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		form = requestResetForm()
		if request.method == "POST":
			if form.validate_on_submit():
				student = Student.query.filter_by(email=form.email.data).first()
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
		app.logger.error('In resetRequest, Error is: {}'.format(e))
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
				student.password = hashed_password
				app.logger.info('In resetToken, commiting new password to DB for {}'.format(student))
				db.session.commit()
				flash('Your password has been updated successfully!', 'success')
				return redirect(url_for('login'))
			else:
				app.logger.info('In resetToken, form is NOT valid. form.errors:{}'.format(form.errors))
				flash('There was an error, see details below.', 'danger')
		return render_template('resetToken.html', title="Reset Password", form=form)
	except Exception as e:
		app.logger.error('In resetToken, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))

@app.route('/CreateAdminAccount', methods=['GET', 'POST'])
def createAdminAccount():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		# check if an admin already exists
		admin = Admin.query.count()
		if admin:
			return redirect(url_for('home'))

		form = createAdminForm()
		if request.method == "POST":
			if form.validate_on_submit():
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				# create admin
				admin = Admin(adminId=form.id.data, password=hashed_password)
				app.logger.info('In Create Admin Account, adding new Admin to DB. Admin is: {}'.format(admin))
				db.session.add(admin)
				# create user
				user = User(userId=form.id.data, userType="admin")
				app.logger.info('In Create Admin Account, adding new User to DB. User is: {}'.format(user))
				db.session.add(user)
				db.session.commit()
				flash('Admin account was created successfully!', 'success')
				return redirect(url_for('login'))
			else:
				app.logger.info('In Create Admin Account, form is NOT valid. form.errors:{}'.format(form.errors))
				flash('There was an error, see details below.', 'danger')
		return render_template('/admin/createAdminAccount.html', title="Create Admin Account", form=form)
	except Exception as e:
		app.logger.error('In createAdminAccount, Error is: {}'.format(e))
		db.session.rollback()
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
				userToLogIn = User.query.filter_by(userId=form.id.data.strip()).first()
				if userToLogIn:
					if userToLogIn.userType == "admin":
						adminUser = Admin.query.filter_by(adminId=userToLogIn.userId).first()
						if bcrypt.check_password_hash(adminUser.password, form.password.data):
							app.logger.info('In Login, admin {} credentials were correct, logging in'.format(adminUser))
							login_user(userToLogIn)
							app.logger.info('In Login, admin {} logged in successfully'.format(adminUser))
							return redirect(url_for('home'))
						else:
							app.logger.info('In Login, admin {} login was unsuccessful, password incorrect'.format(adminUser))
							flash('Login unsuccessful: password is incorrect.', 'danger')
					elif userToLogIn.userType == "student":
						studentUser = Student.query.filter_by(studentId=userToLogIn.userId).first()
						if bcrypt.check_password_hash(studentUser.password, form.password.data):
							app.logger.info('In Login, student {} credentials were correct, logging in'.format(studentUser))
							login_user(userToLogIn)
							app.logger.info('In Login, student {} logged in successfully'.format(studentUser))
							return redirect(url_for('home'))
						else:
							app.logger.info('In Login, student {} login was unsuccessful, password incorrect'.format(studentUser))
							flash('Login unsuccessful: password is incorrect.', 'danger')
					else:
						flash('userType is not recognized for this user.', 'danger')
				else:
					app.logger.info('In Login, could not login, user {} not registred'.format(userToLogIn))
					flash('Login unsuccessful: user not registered.', 'danger')
			else:
				app.logger.info('In Login, form is NOT valid. form.errors:{}'.format(form.errors))
				if 'csrf_token' in form.errors:
					flash('Error: csrf token expired, please re-enter your credentials.', 'danger')
				else:	
					flash('There was an error, see details below.', 'danger')
		return render_template('login.html', title="Login", form=form)
	except Exception as e:
		app.logger.error('In login, Error is: {}'.format(e))
		return redirect(url_for('errorPage'))


@app.route('/ProposedProjects/<id>/Supervisors', methods=['POST', 'GET'])
def getProposedProjectSupervisors(id):
	try:
		supervisorProposedProject = SupervisorProposedProject.query.filter_by(proposedProjectId=id).all()
		supervisors = [Supervisor.query.filter_by(id=s.supervisorId).first() for s in supervisorProposedProject]
		supervisorSchema = SupervisorSchema(many=True)
		result = supervisorSchema.dump(supervisors)
		return jsonify(result.data)
	except Exception as e:
		app.logger.error('In getProposedProjectSupervisors with id: {}, Error is: {}'.format(id, e))
		return "{}"

def copy_image(sourcePath, destinationFolder, destinationName):
	if not os.path.exists(destinationFolder):
		try:
			os.makedirs(destinationFolder)
		except Exception as e:
			app.logger.error('In copy_image, could not make dir {}, Error is: {}'.format(destinationFolder, e))
	try:
		copyfile(sourcePath, os.path.join(destinationFolder, destinationName))
		app.logger.info('In copy_image, file {} was copied successfully to {}'.format(sourcePath, os.path.join(destinationFolder, destinationName)))
	except Exception as e:
		app.logger.error('In copy_image, could not copyfile {}, Error is: {}'.format(sourcePath, e))
	

def save_image(form_image, folder):
	random_hex = secrets.token_hex(8)
	_, imageExt = os.path.splitext(form_image.filename)
	imageName = random_hex + imageExt
	imageFolder = os.path.join(app.root_path, 'static', 'images', folder)
	
	if not os.path.exists(imageFolder):
		try:
			os.makedirs(imageFolder)
		except Exception as e:
			app.logger.error('In save_image, could not make dir {}, Error is: {}'.format(imageFolder, e))

	imagePath = os.path.join(imageFolder, imageName)
	# if this file name is already taken, try maximum 20 other random file names
	for i in range(20):
		if not os.path.isfile(imagePath):
			break
		imageName = secrets.token_hex(8) + imageExt
		imagePath = os.path.join(imageFolder, imageName)

	app.logger.info('In save_image, saving {}'.format(imagePath))
	form_image.save(imagePath)

	return imageName

def getRegistrationSemester():
	currentMonth = int(datetime.datetime.now().strftime("%m"))
	if currentMonth >= 1 and currentMonth <= 6:
		return "Spring"
	else:
		return "Winter"

def getRegistrationYear():
	currentMonth = int(datetime.datetime.now().strftime("%m"))
	currentYear = int(datetime.datetime.now().strftime("%Y"))
	if currentMonth >= 1 and currentMonth <= 6:
		return str(currentYear)
	else:
		return str(currentYear+1)

@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		form = RegistrationForm()
		#projectTitleChoices = [(str(s.id), s.title) for s in ProposedProject.query.all()]
		projectTitleChoices = []
		projectTitleChoices.insert(0, ('', 'NOT CHOSEN'))
		form.projectTitle.choices = projectTitleChoices
		registrationSemester = getRegistrationSemester()
		registrationYear = getRegistrationYear()
		form.semester.choices = [(registrationSemester, registrationSemester)]
		form.year.choices = [(registrationYear, registrationYear)]
		if(request.method == 'POST'):
			form.email.data = form.email.data.strip()
			if form.validate_on_submit():
				app.logger.info('In register, form is valid.')
				projectId = None

				#########################################################################################
				# for now, students can't choose a project themselves, make sure a title is never chosen
				#########################################################################################
				form.projectTitle.data = None

				# some project was chosen			
				if form.projectTitle.data:
					proposedProject = ProposedProject.query.filter_by(id=form.projectTitle.data).first()
					# is another student from the same project already registred?
					projectExists = Project.query.filter_by(year=registrationYear, semester=registrationSemester, title=proposedProject.title).first()
					if not projectExists:
						project = Project(title=proposedProject.title, semester=registrationSemester, year=registrationYear)
						db.session.add(project)
						db.session.commit()
					projectId = Project.query.filter_by(year=registrationYear, semester=registrationSemester, title=proposedProject.title).first().id
				picFile = None
				if form.profilePic.data:
					picFile = save_image(form.profilePic.data, "profile")
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				student = Student(studentId=form.studentId.data, password=hashed_password, firstNameHeb=form.firstNameHeb.data, lastNameHeb=form.lastNameHeb.data, firstNameEng=form.firstNameEng.data.capitalize(), lastNameEng=form.lastNameEng.data.capitalize(), academicStatus=form.academicStatus.data, faculty=form.faculty.data, cellPhone=form.cellPhone.data, email=form.email.data, semester=registrationSemester, year=registrationYear, profilePic=picFile)
				user = User(userId=form.studentId.data, userType="student")
				app.logger.info('In register, adding new Student to DB. Student is: {}'.format(student))
				db.session.add(student)
				app.logger.info('In register, adding new User to DB. User is: {}'.format(user))
				db.session.add(user)
				db.session.commit()
				# register the new student in this project
				if projectId:
					studentProject = StudentProject(studentId=student.id, projectId=projectId)
					app.logger.info('In register, adding new StudentProject to DB. studentProject is: {}'.format(studentProject))
					db.session.add(studentProject)
					db.session.commit()	
				flash('Account created successfully!', 'success')
				return redirect(url_for('login'))
			else:
				app.logger.info('In Register, form is NOT valid. form.errors:{}'.format(form.errors))
				if 'csrf_token' in form.errors:
					flash('Error: csrf token expired, please re-send the form.', 'danger')
				else:	
					flash('There was an error, see details below.', 'danger')
		return render_template('register.html', title="Registration", form=form) 
	except Exception as e:
		app.logger.error('In register, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))

@app.route('/EditAccount', methods=['GET', 'POST'])
def editAccount():
	if not current_user.is_authenticated or current_user.userType == "admin":
		return redirect(url_for('login'))
	try:
		student = Student.query.filter_by(studentId=current_user.userId).first()
		form = EditAccountForm()
		if request.method == 'POST':
			form.email.data = form.email.data.strip()
			if form.validate_on_submit():
				app.logger.info('In Edit Account, form is valid.')
				if student.studentId != form.studentId.data:
					studentWithSameId = Student.query.filter_by(studentId=form.studentId.data).first()
					if studentWithSameId:
						flash('There is already a student with the same ID!', 'danger')
						return redirect(url_for('editAccount'))
				if student.email != form.email.data:
					studentWithSameEmail = Student.query.filter_by(email=form.email.data).first()
					if studentWithSameEmail:
						flash('This email is already used by another student!', 'danger')
						return redirect(url_for('editAccount'))

				picFile = student.profilePic
				if form.profilePic.data:				
					# delete old profile picture
					if picFile is not None:
						picFolder = os.path.join(app.root_path, 'static', 'images', 'profile')
						try:
							os.remove(os.path.join(picFolder, picFile))
						except OSError as e:
							app.logger.error('In Edit Account, could not delete old profile picture {}, Error is: {}'.format(os.path.join(picFolder, picFile), e))
					picFile = save_image(form.profilePic.data, "profile")
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				student.studentId = form.studentId.data
				# update this user in USERS table
				user = User.query.filter_by(userId=student.studentId)
				user.userId = form.studentId.data
				current_user.userId = form.studentId.data
				
				student.password = hashed_password
				student.firstNameHeb = form.firstNameHeb.data
				student.lastNameHeb = form.lastNameHeb.data
				student.firstNameEng = form.firstNameEng.data.capitalize()
				student.lastNameEng = form.lastNameEng.data.capitalize()

				student.academicStatus = form.academicStatus.data
				student.faculty = form.faculty.data
				student.cellPhone = form.cellPhone.data
				student.email = form.email.data
				student.profilePic = picFile

				app.logger.info('In Edit Account, commiting student changes. updated student will be: {}'.format(student))
				db.session.commit()
				flash('Your account was updated successfully!', 'success')
				return redirect(url_for('home'))
			else:
				app.logger.info('In Edit Account, form is NOT valid. form.errors:{}'.format(form.errors))
				if 'csrf_token' in form.errors:
					flash('Error: csrf token expired, please re-enter your credentials.', 'danger')
				else:	
					flash('There was an error, see details below.', 'danger')
		elif request.method == 'GET':
			app.logger.info('In Edit Account, filling fields with student details')
			form.studentId.data = student.studentId
			form.firstNameHeb.data = student.firstNameHeb
			form.lastNameHeb.data = student.lastNameHeb
			form.firstNameEng.data = student.firstNameEng
			form.lastNameEng.data = student.lastNameEng
			form.academicStatus.data = student.academicStatus
			form.faculty.data = student.faculty
			form.cellPhone.data = student.cellPhone
			form.email.data = student.email

		return render_template('editAccount.html', title="Edit Account", form=form, student=student)
	except Exception as e:
		app.logger.error('In editAccount, Error is: {}'.format(e))
		db.session.rollback()
		return redirect(url_for('errorPage'))