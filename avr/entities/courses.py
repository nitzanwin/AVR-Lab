import os
import json
import traceback
from flask import render_template, url_for, flash, redirect, request, jsonify
import flask_login
from avr.forms import (addCourseForm, editCourseForm, deleteCourseForm)
from avr import database, utils

from avr import app, db, bcrypt, mail

def manageCourses():
	if not utils.check_user_lab_admin():
		return redirect(url_for('login'))
	try:
		admin = utils.check_user_admin()
		lab = None if not utils.check_user_lab() else database.getLabByAcronym(flask_login.current_user.userId)
		addForm = addCourseForm()
		editForm = editCourseForm()
		deleteForm = deleteCourseForm()
		addFormErrors = False
		editFormErrorCourseId = ''

		# get Labs
		allLabs = database.getAllLabs()
		allLabsChoices = [(str(l.id), l.acronym) for l in allLabs]
		editForm.new_lab.choices = allLabsChoices
		addForm.new_lab.choices = allLabsChoices

		if (request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editCourseForm':
				course = database.getCourseById(editForm.courseId.data)

				if not course:
					app.logger.error(
						'In manageCourses, in editForm, tried to edit a course with id {} that does not exist in the db'.format(
							editForm.courseId.data))
					flash("Error: Course with id {} is not in the db.".format(editForm.courseId.data), 'danger')
					return redirect(url_for('manageCourses'))

				if editForm.validate_on_submit():
					database.updateCourse(course.id, {
						"number": editForm.new_number.data,
						"name": editForm.new_name.data,
						"lab": editForm.new_lab.data
					})

					flash('Course was updated successfully!', 'success')
					return redirect(url_for('manageCourses'))
				else:
					app.logger.info(
						'In managecourses, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					editFormErrorCourseId = editForm.courseId.data
					if 'csrf_token' in editForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:
						flash('There was an error, see details below.', 'danger')


			elif formName == 'addCourseForm':
				if addForm.validate_on_submit():
					newCourse = {
						"name": addForm.new_name.data,
						"number": addForm.new_number.data,
						"lab": addForm.new_lab.data
					}
					database.addCourse(newCourse)

					flash('Course was created successfully!', 'success')
					return redirect(url_for('manageCourses'))
				else:
					addFormErrors = True
					app.logger.info('In manageCourses, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
					if 'csrf_token' in addForm.errors:
						flash('Error: csrf token expired, please re-send the form.', 'danger')
					else:
						flash('There was an error, see details below.', 'danger')
		return render_template('/admin/courses.html', title="Manage Courses", addForm=addForm,
							   editForm=editForm, deleteForm=deleteForm, addFormErrors=addFormErrors,
							   editFormErrorCourseId=editFormErrorCourseId, admin=admin, lab=lab)
	except Exception as e:
		app.logger.error('In manageCourses, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


def getCoursesTableData():
	if not utils.check_user_lab_admin():
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')

		totalResults, results = database.getCoursesTableData(sort, order, limit, offset, filters)
		rows = []
		for result in results:
			lab = None
			if result.lab:
				lab = database.getLabById(result.lab).acronym
			rows.append({
				"name": result.name,
				"number": result.number,
				"lab": lab,
				"btnEdit": f"<button type='button' onclick='getCourseData({result.id})' name='btnEdit' class='btn btn-primary' data-toggle='modal' data-target='#editCourseModal'><i class='fa fa-edit fa-fw'></i> Edit</button>",
				"btnDelete": f"<button type='button' onclick='deleteCourse({result.id})' name='btnDelete' class='btn btn-danger' data-toggle='modal' data-target='#deleteCourseModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		return jsonify(
			total=totalResults,
			rows=rows,
			filterOptions={
				"lab": database.getLabFilter()
			}
		)

	except Exception as e:
		app.logger.error('In getCoursesTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])

def getCourseData(id):
	if not utils.check_user_lab_admin():
		return redirect(url_for('login'))
	try:
		course = database.getCourseById(id)
		courseData = {
			"id": course.id,
			"name": course.name,
			"number": course.number,
			"lab": course.lab
		}

		return jsonify(courseData)

	except Exception as e:
		app.logger.error('In getCourseData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})

def deleteCourse():
	if not utils.check_user_lab_admin():
		return redirect(url_for('login'))
	try:
		deleteForm = deleteCourseForm()
		course = database.getCourseById(deleteForm.deleteCourseId.data)
		if course:
			app.logger.info('In deleteCourse, deleting {}'.format(course))
			database.deleteCourse(course.id)
			flash('Course was deleted successfully!', 'primary')
		else:
			app.logger.error(
				'In deleteCourse, could not delete course with id {}, because there is no course with this id'.format(
					deleteForm.deleteCourseId.data))
			flash("Error: can't delete, course id {} is not in the db".format(deleteForm.deleteCourseId.data),
				  'danger')
		return redirect(url_for('manageCourses'))
	except Exception as e:
		app.logger.error('In deleteCourse, Error is: {}'.format(e))
		return redirect(url_for('errorPage'))