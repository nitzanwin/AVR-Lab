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
import traceback


@app.route('/logout', methods=['GET'])
def logout():
	logout_user()
	return redirect(url_for('login'))


@app.route('/Admin', methods=['GET'])
def admin():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	return redirect(url_for('labOverview'))


@app.route('/Admin/Overview', methods=['GET'])
def labOverview():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	overview = database.getLabOverview()
	return render_template("/admin/labOverview.html", overview=overview)


@app.route('/Admin/Supervisors/Delete', methods=['POST'])
def deleteSupervisor():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteSupervisorForm()
		supervisor = database.getSupervisorById(deleteForm.deleteSupervisorId.data)
		if supervisor:
			deleteResult = database.deleteSupervisor(supervisor.id)			
			if deleteResult == "deleted":
				flash('Supervisor was deleted successfully!', 'primary')
			else:
				flash('Supervisor has related projects, it was NOT deleted. Instead, it became not active.', 'info')
		else:
			app.logger.info('In deleteSupervisor, could not delete supervisor with id {}, because there is no supervisor with this id'.format(deleteForm.deleteSupervisorId.data))
			flash("Error: can't delete, supervisor id is not in the db", 'danger')
		return redirect(url_for('manageSupervisors'))
	except Exception as e:
		app.logger.error('In deleteSupervisor, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Admin/Supervisors/<int:id>/json', methods=['GET', 'POST'])
def getSupervisorData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		supervisor = database.getSupervisorById(id)
		supervisorData = { 
			"id": supervisor.id,
			"supervisorId": supervisor.supervisorId,
			"firstNameHeb": supervisor.firstNameHeb,
			"lastNameHeb": supervisor.lastNameHeb,
			"firstNameEng": supervisor.firstNameEng,
			"lastNameEng": supervisor.lastNameEng,
			"email": supervisor.email or "",
			"phone": supervisor.phone or "",
			"status": supervisor.status
		}
		return jsonify(supervisorData)
	except Exception as e:
		app.logger.error('In getSupervisorData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})


@app.route('/Admin/Supervisors/json', methods=['GET', 'POST'])
def getSupervisorsTableData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getSupervisorsTableData(sort, order, limit, offset, filters)	
		rows = []
		for result in results:
			rows.append({
				"status": result.status,
				"supervisorId": result.supervisorId,
				"firstNameHeb": result.firstNameHeb,
				"lastNameHeb": result.lastNameHeb,
				"email": result.email or "",
				"btnEdit": f"<button type='button' onclick='getSupervisorData({result.id})' name='btnEdit' class='btn btn-primary' data-toggle='modal' data-target='#editSupervisorModal'><i class='fa fa-edit fa-fw'></i> Edit</button>",
				"btnDelete": f"<button type='button' onclick='deleteSupervisor({result.id})' name='btnDelete' class='btn btn-danger' data-toggle='modal' data-target='#deleteSupervisorModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		# get filters options for the table
		# ------- status filters
		status = [{"value": "", "text": "ALL"}, {"value": "active", "text": "active"}, {"value": "not active", "text": "not active"}]

		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions={
				"status": status
			})
			
	except Exception as e:
		app.logger.error('In getSupervisorsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])	


@app.route('/Admin/Supervisors', methods=['GET', 'POST'])
def manageSupervisors():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		addForm = addSupervisorForm()
		editForm = editSupervisorForm()
		deleteForm = deleteSupervisorForm()
		addFormErrors = False
		editFormErrorSupervisorId = ''
		if(request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editSupervisorForm':
				supervisor = database.getSupervisorById(editForm.id.data)
				if not supervisor:
					app.logger.error('In manageSupervisors, in editForm, tried to edit a supervisor with id {} that does not exist in the db'.format(editForm.id.data))
					flash("Error: supervisor with id {} is not in the db.".format(editForm.id.data), 'danger')
					return redirect(url_for('manageSupervisors'))
				if editForm.validate_on_submit():
					database.updateSupervisor(supervisor.id, {
						"supervisorId": editForm.supervisorId.data,
						"firstNameEng": editForm.firstNameEng.data.capitalize(),
						"lastNameEng": editForm.lastNameEng.data.capitalize(),
						"firstNameHeb": editForm.firstNameHeb.data,
						"lastNameHeb": editForm.lastNameHeb.data,
						"email": editForm.email.data.strip(),
						"phone": editForm.phone.data,
						"status": editForm.status.data,
					})
					app.logger.info('In manageSupervisors, in editForm, commiting supervisor {} changes'.format(supervisor))
					flash('Supervisor was updated successfully!', 'success')
					return redirect(url_for('manageSupervisors'))
				else:
					app.logger.info('In manageSupervisors, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					editFormErrorSupervisorId = editForm.id.data
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')
			if formName == 'addSupervisorForm':
				if addForm.validate_on_submit():					
					database.addSupervisor({
						"supervisorId": addForm.newSupervisorId.data,
						"firstNameEng": addForm.newFirstNameEng.data.capitalize(),
						"lastNameEng": addForm.newLastNameEng.data.capitalize(),
						"firstNameHeb": addForm.newFirstNameHeb.data,
						"lastNameHeb": addForm.newLastNameHeb.data,
						"email": addForm.newEmail.data.strip(),
						"phone": addForm.newPhone.data,
						"status": addForm.newStatus.data
					})
					flash('Supervisor created successfully!', 'success')
					return redirect(url_for('manageSupervisors'))
				else:
					app.logger.info('In manageSupervisors, addForm is NOT valid. addForm.errors: {}'.format(addForm.errors))
					addFormErrors = True
					if 'csrf_token' in addForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')
		return render_template('/admin/supervisors.html', title="Manage Supervisors", editForm=editForm, deleteForm=deleteForm, addForm=addForm, editFormErrorSupervisorId=editFormErrorSupervisorId, addFormErrors=addFormErrors)
	except Exception as e:
		app.logger.error('In manageSupervisors, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Admin/Students/Delete', methods=['POST'])
def deleteStudent():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteStudentForm()
		student = database.getStudentById(deleteForm.deleteStudentId.data)
		if student:
			# delete profile pic if exists
			utils.delete_profile_image(student.profilePic)
			database.deleteStudent(student.id)
			app.logger.info('In deleteStudent, deleting student {}'.format(student))
			flash('Student was deleted successfully!', 'success')
		else:
			app.logger.info('In deleteStudent, could not delete student with id {}, because there is no student with this id'.format(deleteForm.deleteStudentId.data))
			flash("Error: can't delete, student with id {} is not in the db".format(deleteForm.deleteStudentId.data), 'danger')
		return redirect(url_for('manageStudents'))
	except Exception as e:
		app.logger.error('In deleteStudent, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Admin/Students/<int:id>/json', methods=['GET', 'POST'])
def getStudentData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		student = database.getStudentById(id)
		lastProjects = [{"id": p.id, "title": p.title} for p in student.projects]
		studentData = { 
			"id": student.id,
			"profilePic": student.profilePic or "default.png",
			"year": student.year or "",
			"semester": student.semester or "",
			"studentId": student.studentId,
			"firstNameHeb": student.firstNameHeb,
			"lastNameHeb": student.lastNameHeb,
			"firstNameEng": student.firstNameEng,
			"lastNameEng": student.lastNameEng,
			"email": student.email,
			"lastProjects": lastProjects
		}
		return jsonify(studentData)
	except Exception as e:
		app.logger.error('In getStudentsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})


@app.route('/Admin/StudentsForProject/json', methods=['GET', 'POST'])
def getStudentsTableForProjectData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getStudentsTableForProjectData(sort, order, limit, offset, filters)
		
		rows = []
		for result in results:
			profilePic = f"<img style='width:50px;height:50px;' src='/static/images/profile/default.png' alt='default profile pic'>"
			if result.profilePic:	
				profilePic = f"<img style='width:50px;height:50px;' src='/static/images/profile/{result.profilePic}' alt='{result.profilePic}'>"

			rows.append({
				"profilePic": profilePic,
				"registrationYear": result.year,
				"registrationSemester": result.semester,
				"studentId": result.studentId,
				"firstNameHeb": result.firstNameHeb,
				"lastNameHeb": result.lastNameHeb,
				"id": result.id
			})

		# get filters options for the table
		filterOptions = database.getStudentsTableForProjectFilters()

		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions=filterOptions
		)
		
	except Exception as e:
		app.logger.error('In getStudentsTableForProjectData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])	


@app.route('/Admin/Students/json', methods=['GET', 'POST'])
def getStudentsTableData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getStudentsTableData(sort, order, limit, offset, filters)
		
		rows = []
		for result in results:
			profilePic = f"<img style='width:50px;height:50px;' src='/static/images/profile/default.png' alt='default profile pic'>"
			if result.profilePic:	
				profilePic = f"<img style='width:50px;height:50px;' src='/static/images/profile/{result.profilePic}' alt='{result.profilePic}'>"

			lastProjectTitle = f"<a href='javascript:void(0);' class='badge badge-warning px-2' style='padding: 1em 0;'>NO PROJECT</a>"
			if result.lastProjectTitle:
				lastProjectTitle = f"<a href='javascript:void(0);' onclick='getProjectData({result.lastProjectId})' class='badge badge-primary px-2' name='studentProjectBadge' style='background-color: #9d6bff;padding: 1em 0;'>{result.lastProjectTitle}</a>"

			rows.append({
				"profilePic": profilePic,
				"year": result.year or "----",
				"semester": result.semester or "----",
				"studentId": result.studentId,
				"firstNameHeb": result.firstNameHeb,
				"lastNameHeb": result.lastNameHeb,
				"lastProjectTitle": lastProjectTitle,
				"lastProjectStatus": result.lastProjectStatus or "----",
				"btnEdit": f"<button type='button' onclick='getStudentData({result.id})' name='btnEdit' class='btn btn-primary'><i class='fa fa-edit fa-fw'></i> Edit</button>",
				"btnDelete": f"<button type='button' onclick='deleteStudent({result.id})' name='btnDelete' class='btn btn-danger' data-toggle='modal' data-target='#deleteStudentModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		# get filters options for the table
		filterOptions = database.getStudentsTableFilters()
		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions=filterOptions
		)
		
	except Exception as e:
		app.logger.error('In getStudentsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])



@app.route('/Admin/Students', methods=['GET', 'POST'])
def manageStudents():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		totalStudents = database.getStudentsCount()
		editForm = editStudentForm()
		edit_ProjectForm = editProjectForm()
		courses = database.getAllCourses()
		deleteForm = deleteStudentForm()
		editFormErrorStudentId = ''
		editProjectErrorId = ''
		currentSemester = utils.getRegistrationSemester()
		currentYear = utils.getRegistrationYear()
		semesterChoices = [("Winter", "Winter"), ("Spring", "Spring")]
		if currentSemester == "Spring":
			semesterChoices.reverse()

		allSupervisors = database.getAllSupervisors()
		supervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in allSupervisors]
		supervisorsChoices.insert(0, ('', ''))

		edit_ProjectForm.year.choices = [(currentYear, currentYear), (str(int(currentYear)+1),str(int(currentYear)+1)), (str(int(currentYear)+2),str(int(currentYear)+2))]
		edit_ProjectForm.semester.choices = semesterChoices
		edit_ProjectForm.supervisor1.choices = supervisorsChoices
		edit_ProjectForm.supervisor2.choices = supervisorsChoices
		edit_ProjectForm.supervisor3.choices = supervisorsChoices


		if(request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editStudentForm':
				student = database.getStudentById(editForm.id.data)
				if not student:
					app.logger.error('In manageStudents, in editForm, tried to edit a student with id {} that does not exist in the db'.format(editForm.id.data))
					flash("Error: student with id {} doesn't exist in the db.".format(editForm.id.data), 'danger')
					return redirect(url_for('manageStudents'))
				if editForm.validate_on_submit():
					database.updateStudent(student.id, {
						"studentId": editForm.studentId.data,
						"firstNameEng": editForm.firstNameEng.data.capitalize(),
						"lastNameEng": editForm.lastNameEng.data.capitalize(),
						"firstNameHeb": editForm.firstNameHeb.data,
						"lastNameHeb": editForm.lastNameHeb.data,
						"email": editForm.email.data
					})
					
					app.logger.info('In manageStudents, commiting student {} changes'.format(student))
					flash('Student was updated successfully!', 'success')
					return redirect(url_for('manageStudents'))
				else:
					app.logger.info('In manageStudents, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					editFormErrorStudentId = editForm.id.data
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')

		return render_template('/admin/students.html', title="Manage Students", editForm=editForm, editProjectForm=edit_ProjectForm, courses=courses, deleteForm=deleteForm, editFormErrorStudentId=editFormErrorStudentId, totalStudents=totalStudents)
	except Exception as e:
		app.logger.error('In manageStudents, Error is: {}'.format(e))
		return redirect(url_for('errorPage'))


@app.route('/Admin/Projects/<int:id>/json', methods=['GET', 'POST'])
def getProjectData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		project = database.getProjectById(id)
		studentsInProject = [{"id": s.id, "fullNameHeb": s.firstNameHeb+" "+s.lastNameHeb} for s in project.students]
		for student in studentsInProject:
			student["courseId"] = database.getCourseIdForStudentInProject(id, student["id"])
		supervisors = [{"id": s.id, "fullNameEng": s.firstNameEng+" "+s.lastNameEng} for s in project.supervisors]

		projectData = { 
			"id": project.id,
			"image": project.image,
			"year": project.year or "",
			"semester": project.semester or "",
			"title": project.title,
			"grade": project.grade,
			"comments": project.comments,
			"status": project.status,
			"requirementsDoc": project.requirementsDoc or False,
			"firstMeeting": project.firstMeeting or False,
			"halfwayPresentation": project.halfwayPresentation or False,
			"finalMeeting": project.finalMeeting or False,
			"projectReport": project.projectReport or False,
			"equipmentReturned": project.equipmentReturned or False,
			"projectDoc": project.projectDoc or False,
			"gradeStatus": project.gradeStatus or False,
			"students": studentsInProject,
			"supervisors": supervisors
		}

		return jsonify(projectData)

	except Exception as e:
		app.logger.error('In getProjectData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})


@app.route('/Admin/Projects/Delete', methods=['POST'])
def deleteProject():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteProjectForm()
		project = database.getProjectById(deleteForm.deleteProjectId.data)
		
		if project:
			# delete project image
			utils.delete_project_image(project.image)
			# delete project 
			app.logger.info('In deleteProject, deleting {}'.format(project))
			database.deleteProject(project.id)
			flash('Project was deleted successfully!', 'primary')
		else:
			app.logger.error('In deleteProject, could not delete project with id {}, because there is no project with this id'.format(deleteForm.deleteProjectId.data))
			flash("Error: can't delete, project id {} is not in the db".format(deleteForm.deleteProjectId.data), 'danger')
		return redirect(url_for('manageProjects'))
	except Exception as e:
		app.logger.error('In deleteProject, Error is: {}'.format(e))
		return redirect(url_for('errorPage'))
	

@app.route('/Admin/Projects/json', methods=['GET', 'POST'])
def getProjectsTableData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getProjectsTableData(sort, order, limit, offset, filters)
		
		rows = []
		for result in results:
			supervisors = database.getProjectById(result.id).supervisorsFullNameEng
			
			rows.append({
				"image": f"<img style='width:80px;height:70px;' src='/static/images/projects/{result.image}' alt='{result.image}'" if result.image else "",
				"year": result.year,
				"semester": result.semester ,
				"title": result.title,
				"status": result.status,
				"supervisorsNames": ",<br>".join(supervisors),
				"btnEdit": f"<button type='button' onclick='getProjectData({result.id})' name='btnEdit' class='btn btn-primary' data-toggle='modal' data-target='#editProjectModal'><i class='fa fa-edit fa-fw'></i> Edit</button>",
				"btnDelete": f"<button type='button' onclick='deleteProject({result.id})' name='btnDelete' class='btn btn-danger' data-toggle='modal' data-target='#deleteProjectModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		# get filters options for the table
		filterOptions = database.getProjectsTableFilters()

		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions=filterOptions
		)
		
	except Exception as e:
		app.logger.error('In getProjectsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])



@app.route('/Admin/Projects', methods=['GET', 'POST'])
def manageProjects():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		courses = database.getAllCourses()
		addForm = addProjectForm()
		editForm = editProjectForm()
		deleteForm = deleteProjectForm()
		addFormErrors = False
		editFormErrorProjectId = ''
		edit_studentForm = editStudentForm()
		
		currentSemester = utils.getRegistrationSemester()
		currentYear = utils.getRegistrationYear()
		semesterChoices = [("Winter", "Winter"), ("Spring", "Spring")]
		if currentSemester == "Spring":
			semesterChoices.reverse()
		addForm.new_title.choices = [(str(s.id), s.title) for s in database.getAllProposedProjects()]
		addForm.new_year.choices = [(currentYear, currentYear), (str(int(currentYear)+1),str(int(currentYear)+1)), (str(int(currentYear)+2),str(int(currentYear)+2))]
		addForm.new_semester.choices = semesterChoices

		allSupervisors = database.getAllSupervisors()
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

		if(request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editProjectForm':
				project = database.getProjectById(editForm.projectId.data)

				if not project:
					app.logger.error('In manageProjects, in editForm, tried to edit a project with id {} that does not exist in the db'.format(editForm.projectId.data))
					flash("Error: project with id {} is not in the db.".format(editForm.projectId.data), 'danger')
					return redirect(url_for('manageProjects'))

				if editForm.validate_on_submit():
					studentsIds = request.form.getlist("students")
					studentsCoursesIds = request.form.getlist("studentsCoursesIds")
					if studentsIds and not studentsCoursesIds:
						flash("Error: students can't be added to a project without a course number.", 'danger')		
						return redirect(url_for('manageProjects'))

					projectImage = project.image
					if editForm.image.data:
						# delete old image if exists
						app.logger.info('In manageProjects, in editForm, deleting old project image')
						utils.delete_project_image(projectImage)
						projectImage = utils.save_form_image(editForm.image.data, "projects")
					
					database.updateProject(project.id, {
						"title": editForm.title.data,
						"year": editForm.year.data,
						"semester": editForm.semester.data,
						"comments": editForm.comments.data,
						"grade": editForm.grade.data,
						"image": projectImage
					})

					# update students in project
					studentsInProject = []
					for i in range(len(studentsIds)):
						studentsInProject.append({
							"id": studentsIds[i],
							"courseId": studentsCoursesIds[i]
						})
					database.updateProjectStudents(project.id, studentsInProject)
					
					# update supervisors in project
					supervisorsIds = set()
					if editForm.supervisor1.data:
						supervisorsIds.add(editForm.supervisor1.data)
					if editForm.supervisor2.data:
						supervisorsIds.add(editForm.supervisor2.data)
					if editForm.supervisor3.data:
						supervisorsIds.add(editForm.supervisor3.data)
					database.updateProjectSupervisors(project.id, supervisorsIds)

					# update status
					database.updateProjectStatus(project.id, {
						"requirementsDoc": editForm.requirementsDoc.data,
						"firstMeeting": editForm.firstMeeting.data,
						"halfwayPresentation": editForm.halfwayPresentation.data,
						"finalMeeting": editForm.finalMeeting.data,
						"projectReport": editForm.projectReport.data,
						"equipmentReturned": editForm.equipmentReturned.data,
						"projectDoc": editForm.projectDoc.data,
						"gradeStatus": editForm.gradeStatus.data
					})

					flash('Project was updated successfully!', 'success')
					if request.form.get('studentsReferrer'):
						return redirect(url_for('manageStudents'))
					else:
						return redirect(url_for('manageProjects'))
				else:
					app.logger.info('In manageProjects, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					editFormErrorProjectId = editForm.projectId.data
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')
					if request.form.get('studentsReferrer'):
						edit_StudentForm = editStudentForm()
						delete_StudentForm = deleteStudentForm()
						editFormErrorStudentId = ''

						return render_template('/admin/students.html', title="Manage Students", editForm=edit_StudentForm, editProjectForm=editForm, courses=courses, deleteForm=delete_StudentForm, editFormErrorStudentId=editFormErrorStudentId, editProjectErrorId=editFormErrorProjectId)

			elif formName == 'addProjectForm':
				if addForm.validate_on_submit():				
					studentsIds = request.form.getlist("students")
					studentsCoursesIds = request.form.getlist("studentsCoursesIds")
					if studentsIds and not studentsCoursesIds:
						flash("Error: students can't be added to a project without a course number.", 'danger')		
						return redirect(url_for('manageProjects'))
					
					# add new project
					projectTitle = dict(addForm.new_title.choices).get(addForm.new_title.data)
					newImageName = None
					# save project image
					matchingProposedProject = database.getProposedProjectByTitle(projectTitle)
					if matchingProposedProject:
						matchingImageName = matchingProposedProject.image
						if matchingImageName:
							newImageName = utils.copy_project_image_from_proposed_project(matchingImageName)
					

					newProject = {
						"title": projectTitle,
						"year": addForm.new_year.data,
						"semester": addForm.new_semester.data,
						"grade": addForm.new_grade.data,
						"comments": addForm.new_comments.data,
						"image": newImageName,
						"requirementsDoc": addForm.new_requirementsDoc.data,
						"firstMeeting": addForm.new_firstMeeting.data,
						"halfwayPresentation": addForm.new_halfwayPresentation.data,
						"finalMeeting": addForm.new_finalMeeting.data,
						"projectReport": addForm.new_projectReport.data,
						"equipmentReturned": addForm.new_equipmentReturned.data,
						"projectDoc": addForm.new_projectDoc.data,
						"gradeStatus": addForm.new_gradeStatus.data,
						"status": "הרשמה"
					}
					
					newProjectId = database.addProject(newProject)

					# add students to project
					studentsInProject = []
					for i in range(len(studentsIds)):
						studentsInProject.append({
							"id": studentsIds[i],
							"courseId": studentsCoursesIds[i]
						})
					database.updateProjectStudents(newProjectId, studentsInProject)

					# add supervisors to project
					supervisorsIds = set()
					if addForm.new_supervisor1.data:
						supervisorsIds.add(addForm.new_supervisor1.data)
					if addForm.new_supervisor2.data:
						supervisorsIds.add(addForm.new_supervisor2.data)
					if addForm.new_supervisor3.data:
						supervisorsIds.add(addForm.new_supervisor3.data)
					database.updateProjectSupervisors(newProjectId, supervisorsIds)
					
					flash('Project was created successfully!', 'success')
					return redirect(url_for('manageProjects'))
				else:
					addFormErrors = True
					app.logger.info('In manageProjects, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
					if 'csrf_token' in addForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:	
						flash('There was an error, see details below.', 'danger')
		return render_template('/admin/projects.html', title="Manage Projects", courses=courses, addForm=addForm, editForm=editForm, deleteForm=deleteForm, addFormErrors=addFormErrors, editFormErrorProjectId=editFormErrorProjectId, editStudentForm=edit_studentForm)
	except Exception as e:
		app.logger.error('In manageProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Admin/ProposedProjects/json', methods=['GET', 'POST'])
def getProposedProjectsTableData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getProposedProjectsTableData(sort, order, limit, offset, filters)
		
		rows = []
		for result in results:
			supervisors = database.getProposedProjectById(result.id).supervisorsFullNameEng
			rows.append({
				"image": f"<img style='width:80px;height:70px;' src='/static/images/proposed_projects/{result.image}' alt='{result.image}'" if result.image else "",
				"title": result.title,
				"description": result.description,
				"supervisorsNames": ",<br>".join(supervisors),
				"btnEdit": f"<button type='button' onclick='getProposedProjectData({result.id})' name='btnEdit' class='btn btn-primary' data-toggle='modal' data-target='#editProposedProjectModal'><i class='fa fa-edit fa-fw'></i> Edit</button>",
				"btnDelete": f"<button type='button' onclick='deleteProposedProject({result.id})' name='btnDelete' class='btn btn-danger' data-toggle='modal' data-target='#deleteProposedProjectModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions={}
		)
		
	except Exception as e:
		app.logger.error('In getProposedProjectsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])	


@app.route('/Admin/ProposedProjects/Delete', methods=['POST'])
def deleteProposedProjects():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteProposedProjectForm()
		proposedProject = database.getProposedProjectById(deleteForm.deleteProposedProjectId.data)
		if proposedProject:
			picFile = proposedProject.image
			# delete image if exists
			if picFile is not None:
				utils.delete_proposed_project_image(picFile)
			
			database.deleteProposedProject(proposedProject.id)
			flash('Proposed Project was deleted successfully!', 'primary')
		else:
			app.logger.info('In deleteProposedProjects, could not delete proposed project with id {}, because there is no proposed project with this id'.format(deleteForm.deleteProposedProjectId.data))
			flash("Error: can't delete, proposed project id is not in the db", 'danger')
		return redirect(url_for('manageProposedProjects'))
	except Exception as e:
		app.logger.error('In deleteProposedProjects, Error is: {}'.format(e))
		return redirect(url_for('errorPage'))
	

@app.route('/Admin/ProposedProjects/<int:id>/json', methods=['GET', 'POST'])
def getProposedProjectData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		proposedProject = database.getProposedProjectById(id)
		supervisors = [{"id": s.id, "fullNameEng": s.firstNameEng+" "+s.lastNameEng} for s in proposedProject.supervisors]

		proposedProjectData = { 
			"id": proposedProject.id,
			"image": proposedProject.image,
			"title": proposedProject.title,
			"description": proposedProject.description,
			"supervisors": supervisors
		}

		return jsonify(proposedProjectData)

	except Exception as e:
		app.logger.error('In getProposedProjectData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})


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
		allSupervisors = database.getAllSupervisors()
		activeSupervisors = database.getActiveSupervisors()
		allSupervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in allSupervisors]
		activeSupervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in activeSupervisors]
		allSupervisorsChoices.insert(0, ('', ''))
		activeSupervisorsChoices.insert(0, ('', ''))

		editForm.supervisor1.choices = allSupervisorsChoices
		editForm.supervisor2.choices = allSupervisorsChoices
		editForm.supervisor3.choices = allSupervisorsChoices 

		addForm.newSupervisor1.choices = activeSupervisorsChoices
		addForm.newSupervisor2.choices = activeSupervisorsChoices
		addForm.newSupervisor3.choices = activeSupervisorsChoices 
		
		if(request.method == 'POST'):
			formName = request.form['pageForm']
			if formName == 'addProposedProjectForm':
				if addForm.validate_on_submit():
					picFile = None
					if addForm.newImage.data:
						app.logger.info('In manageProposedProjects, saving image of new proposed project')
						picFile = utils.save_form_image(addForm.newImage.data, "proposed_projects")
					
					# create new proposed project
					newProposedProjectId = database.addProposedProject({
						"title": addForm.newTitle.data,
						"description": addForm.newDescription.data,
						"image": picFile
					})
					
					# save the supervisors for this proposed project
					supervisorsIds = set()
					if addForm.newSupervisor1.data:
						supervisorsIds.add(int(addForm.newSupervisor1.data))
					if addForm.newSupervisor2.data:
						supervisorsIds.add(int(addForm.newSupervisor2.data))
					if addForm.newSupervisor3.data:
						supervisorsIds.add(int(addForm.newSupervisor3.data))
					database.updateProposedProjectSupervisors(newProposedProjectId, supervisorsIds)
					
					flash('Proposed project created successfully!', 'success')
					return redirect(url_for('manageProposedProjects'))
				else:
					app.logger.info('In manageProposedProjects, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
					if 'csrf_token' in addForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:
						flash('There was an error, see details below.', 'danger')
					addFormErrors = True
			elif formName == 'editProposedProjectForm':
				proposedProject = database.getProposedProjectById(editForm.proposedProjectId.data)

				if not proposedProject:
					app.logger.error('In manageProposedProjects, in editForm, tried to edit a proposed project with id {} that does not exist in the db'.format(editForm.proposedProjectId.data))
					flash("Error: project with id {} is not in the db.".format(editForm.proposedProjectId.data), 'danger')
					return redirect(url_for('manageProposedProjects'))

				if editForm.validate_on_submit():	
					picFile = proposedProject.image
					if editForm.image.data:
						# delete old image if exists
						if picFile is not None:
							utils.delete_proposed_project_image(picFile)
						picFile = utils.save_form_image(editForm.image.data, "proposed_projects")

					database.updateProposedProject(proposedProject.id, {
						"title": editForm.title.data,
						"description": editForm.description.data,
						"image": picFile
					})

					newSupervisorsIds = set()
					if editForm.supervisor1.data:
						newSupervisorsIds.add(int(editForm.supervisor1.data))
					if editForm.supervisor2.data:
						newSupervisorsIds.add(int(editForm.supervisor2.data))
					if editForm.supervisor3.data:
						newSupervisorsIds.add(int(editForm.supervisor3.data))
					database.updateProposedProjectSupervisors(proposedProject.id, newSupervisorsIds)

					flash('Proposed project was updated successfully!', 'success')
					return redirect(url_for('manageProposedProjects'))
				else:
					app.logger.info('In manageProposedProjects, editForm is NOT valid. editForm.errors:{}'.format(editForm.errors))
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:
						flash('There was an error, see details below.', 'danger')
					editFormErrorProposedProjectId = editForm.proposedProjectId.data

		return render_template('/admin/proposedProjects.html', title="Manage Proposed Projects", addForm=addForm, editForm=editForm, deleteForm=deleteForm, addFormErrors=addFormErrors, editFormErrorProposedProjectId=editFormErrorProposedProjectId)
	except Exception as e:
		app.logger.error('In manageProposedProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/ProjectStatus/<int:id>', methods=['GET'])
def projectStatus(id):
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('manageProjects'))
	# user is a student
	try:
		student = database.getStudentByStudentId(current_user.userId)
		project = None
		isStudentEnrolledInProject = database.isStudentEnrolledInProject(id, student.id)
		if not isStudentEnrolledInProject:
			flash("You are not enrolled in the project.", 'danger')
		else:
			project = database.getProjectById(id)

		return render_template('projectStatus.html', title="Project Status", student=student, project=project, isStudentEnrolledInProject=isStudentEnrolledInProject)
	except Exception as e:
		app.logger.error('In projectStatus, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/', methods=['GET'])
def index():
	try:
		proposedProjects = database.getLimitedProposedProjects(5)
		student = None
		admin = None
		if current_user.is_authenticated:
			if current_user.userType == "student":
				student = database.getStudentByStudentId(current_user.userId)
			elif current_user.userType == "admin":
				admin = database.getAdminByAdminId(current_user.userId)
		return render_template('index.html', proposedProjects=proposedProjects, student=student, admin=admin)
	except Exception as e:
		app.logger.error('In index page, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/home', methods=['GET'])
def home():
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('labOverview'))
	# user is a student
	try:
		student =  database.getStudentByStudentId(current_user.userId)
		projects = student.projects
		return render_template('studentHome.html', title="Home", student=student, projects=projects)
	except Exception as e:
		app.logger.error('In home, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/ProposedProjects', methods=['GET'])
def proposedProjects():
	try:
		proposedProjects = database.getAllProposedProjects()
		return render_template('proposedProjects.html', title="Proposed Projects", proposedProjects=proposedProjects)
	except Exception as e:
		app.logger.error('In proposedProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
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
		return redirect(url_for('home'))
	try:
		totalAdmins = database.getAdminsCount()
		# allow **only one** admin to register
		if totalAdmins > 0:
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
						adminUser = database.getAdminByAdminId(userToLogIn.userId)
						if bcrypt.check_password_hash(adminUser.password, form.password.data):
							login_user(userToLogIn)
							return redirect(url_for('home'))
						else:
							app.logger.info('In Login, admin {} login was unsuccessful, password incorrect'.format(adminUser))
							flash('Login unsuccessful: password is incorrect.', 'danger')
					elif userToLogIn.userType == "student":
						studentUser = database.getStudentByStudentId(userToLogIn.userId)
						if bcrypt.check_password_hash(studentUser.password, form.password.data):
							login_user(userToLogIn)
							return redirect(url_for('home'))
						else:
							flash('Login unsuccessful: password is incorrect.', 'danger')
					else:
						flash('userType is not recognized for this user.', 'danger')
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


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		form = RegistrationForm()
		projectTitleChoices = [('', 'NOT CHOSEN')]
		form.projectTitle.choices = projectTitleChoices
		registrationSemester = utils.getRegistrationSemester()
		registrationYear = utils.getRegistrationYear()
		form.semester.choices = [(registrationSemester, registrationSemester)]
		form.year.choices = [(registrationYear, registrationYear)]
		if (request.method == 'POST'):
			form.email.data = form.email.data.strip()
			if form.validate_on_submit():				
				picFile = None
				if form.profilePic.data:
					picFile = utils.save_form_image(form.profilePic.data, "profile")
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				database.registerStudent({
					"studentId": form.studentId.data,
					"password": hashed_password,
					"firstNameHeb": form.firstNameHeb.data,
					"lastNameHeb": form.lastNameHeb.data,
					"firstNameEng": form.firstNameEng.data.capitalize(),
					"lastNameEng": form.lastNameEng.data.capitalize(),
					"academicStatus": form.academicStatus.data,
					"faculty": form.faculty.data,
					"cellPhone": form.cellPhone.data,
					"email": form.email.data,
					"semester": registrationSemester,
					"year": registrationYear,
					"profilePic": picFile
				})

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
		app.logger.error('In register, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))

@app.route('/EditAccount', methods=['GET', 'POST'])
def editAccount():
	if not current_user.is_authenticated or current_user.userType == "admin":
		return redirect(url_for('login'))
	try:
		student = database.getStudentByStudentId(current_user.userId)
		form = EditAccountForm()

		if request.method == 'POST':
			form.email.data = form.email.data.strip()
			if form.validate_on_submit():
				if student.studentId != form.studentId.data:
					userWithSameId = database.getUserByUserId(form.studentId.data)
					if userWithSameId:
						flash('There is already a user with the same ID!', 'danger')
						return redirect(url_for('editAccount'))
				if student.email != form.email.data:
					studentWithSameEmail = database.getStudentByEmail(form.email.data)
					if studentWithSameEmail:
						flash('This email is already used by another student!', 'danger')
						return redirect(url_for('editAccount'))

				profilePic = student.profilePic
				if form.profilePic.data:				
					# delete old profile image
					utils.delete_profile_image(profilePic)
					# save new profile image	
					profilePic = utils.save_form_image(form.profilePic.data, "profile")
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

				database.updateStudent(student.id, {
					"studentId": form.studentId.data,
					"password": hashed_password,
					"firstNameHeb": form.firstNameHeb.data,
					"lastNameHeb": form.lastNameHeb.data,
					"firstNameEng": form.firstNameEng.data.capitalize(),
					"lastNameEng": form.lastNameEng.data.capitalize(),
					"academicStatus": form.academicStatus.data,
					"faculty": form.faculty.data,
					"cellPhone": form.cellPhone.data,
					"email": form.email.data,
					"profilePic": profilePic
				})
				# update userId in current session
				current_user.userId = form.studentId.data
				app.logger.info('In Edit Account, commiting student changes. updated student will be: {}'.format(student))
				flash('Your account was updated successfully!', 'success')
				return redirect(url_for('home'))
			else:
				app.logger.info('In Edit Account, form is NOT valid. form.errors:{}'.format(form.errors))
				if 'csrf_token' in form.errors:
					flash('Error: csrf token expired, please re-enter your credentials.', 'danger')
				else:	
					flash('There was an error, see details below.', 'danger')
		elif request.method == 'GET':
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
		app.logger.error('In editAccount, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))