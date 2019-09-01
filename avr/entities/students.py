import os
import json
import traceback
import flask_login
from flask import render_template, url_for, flash, redirect, request, jsonify
from avr.forms import RegistrationForm, editStudentForm, editProjectForm, deleteStudentForm, EditAccountForm
from avr import database
from avr import utils
from avr import app, db, bcrypt, mail

def register():
	if flask_login.current_user.is_authenticated:
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


def manageStudents():
	if not utils.check_user_lab_admin():
		return redirect(url_for('login'))
	try:
		admin = utils.check_user_admin()
		lab = None if not utils.check_user_lab() else database.getLabByAcronym(flask_login.current_user.userId)
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
		supervisorsChoices = [(str(s.id), s.firstNameEng + " " + s.lastNameEng) for s in allSupervisors]
		supervisorsChoices.insert(0, ('', ''))

		edit_ProjectForm.year.choices = [(currentYear, currentYear),
										 (str(int(currentYear) + 1), str(int(currentYear) + 1)),
										 (str(int(currentYear) + 2), str(int(currentYear) + 2))]
		edit_ProjectForm.semester.choices = semesterChoices
		edit_ProjectForm.supervisor1.choices = supervisorsChoices
		edit_ProjectForm.supervisor2.choices = supervisorsChoices
		edit_ProjectForm.supervisor3.choices = supervisorsChoices

		if (request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editStudentForm':
				student = database.getStudentById(editForm.id.data)
				if not student:
					app.logger.error(
						'In manageStudents, in editForm, tried to edit a student with id {} that does not exist in the db'.format(
							editForm.id.data))
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
					app.logger.info(
						'In manageStudents, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					editFormErrorStudentId = editForm.id.data
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:
						flash('There was an error, see details below.', 'danger')

		return render_template('/admin/students.html', title="Manage Students", editForm=editForm,
							   editProjectForm=edit_ProjectForm, courses=courses, deleteForm=deleteForm,
							   editFormErrorStudentId=editFormErrorStudentId, totalStudents=totalStudents,
							   admin=admin, lab=lab)
	except Exception as e:
		app.logger.error('In manageStudents, Error is: {}'.format(e))
		return redirect(url_for('errorPage'))


def getStudentsTableData():
	if not utils.check_user_lab_admin():
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


def getStudentsTableForProjectData():
	if not utils.check_user_lab_admin():
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
				"email": result.email,
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

def getStudentData(id):
	if not utils.check_user_lab_admin():
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

def deleteStudent():
	if not utils.check_user_lab_admin():
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

def editAccount():
	if not utils.check_user_student():
		return redirect(url_for('login'))
	try:
		student = database.getStudentByStudentId(flask_login.current_user.userId)
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
				flask_login.current_user.userId = form.studentId.data
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
