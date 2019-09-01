import os
import json
import traceback
import flask_login
from flask import render_template, url_for, flash, redirect, request, jsonify
from avr.forms import addProjectForm, editProjectForm, deleteProjectForm, editStudentForm, deleteStudentForm
from avr import database
from avr import utils
from avr import app, db, bcrypt, mail


def getProjectData(id):
    if not utils.check_user_lab_admin():
        return redirect(url_for('login'))

    try:
        project = database.getProjectById(id)
        studentsInProject = [{"id": s.id, "fullNameHeb": s.firstNameHeb + " " + s.lastNameHeb} for s in
                             project.students]
        for student in studentsInProject:
            student["courseId"] = database.getCourseIdForStudentInProject(id, student["id"])
        supervisors = [{"id": s.id, "fullNameEng": s.firstNameEng + " " + s.lastNameEng} for s in project.supervisors]

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
            "supervisors": supervisors,
            "lab": project.lab
        }

        return jsonify(projectData)

    except Exception as e:
        app.logger.error('In getProjectData, error is: {}\n{}'.format(e, traceback.format_exc()))
        return jsonify({})


def deleteProject():
    if not utils.check_user_lab_admin():
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
            app.logger.error(
                'In deleteProject, could not delete project with id {}, because there is no project with this id'.format(
                    deleteForm.deleteProjectId.data))
            flash("Error: can't delete, project id {} is not in the db".format(deleteForm.deleteProjectId.data),
                  'danger')
        return redirect(url_for('manageProjects'))
    except Exception as e:
        app.logger.error('In deleteProject, Error is: {}'.format(e))
        return redirect(url_for('errorPage'))


def getProjectsTableData():
    if not utils.check_user_lab_admin():
        return redirect(url_for('login'))

    try:
        sort = request.args.get('sort')
        order = request.args.get('order') or "desc"
        limit = request.args.get('limit') or 10
        offset = request.args.get('offset') or 0
        filters = request.args.get('filter')
        lab = None if utils.check_user_admin() else database.getLabByAcronym(flask_login.current_user.userId).id

        totalResults, results = database.getProjectsTableData(sort, order, limit, offset, filters, lab)

        rows = []
        for result in results:
            supervisors = database.getProjectById(result.id).supervisorsFullNameEng
            lab = None
            if result.lab:
                lab = database.getLabById(result.lab).acronym

            rows.append({
                "image": f"<img style='width:80px;height:70px;' src='/static/images/projects/{result.image}' alt='{result.image}'" if result.image else "",
                "year": result.year,
                "semester": result.semester,
                "title": result.title,
                "status": result.status,
                "supervisorsNames": ",<br>".join(supervisors),
                "lab": lab,
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

def getProjectsTableDataWithMails():
    if not utils.check_user_lab_admin():
        return redirect(url_for('login'))

    try:
        sort = request.args.get('sort')
        order = request.args.get('order') or "desc"
        limit = request.args.get('limit') or 10
        offset = request.args.get('offset') or 0
        filters = request.args.get('filter')
        lab = None if utils.check_user_admin() else database.getLabByAcronym(flask_login.current_user.userId).id

        totalResults, results = database.getProjectsTableData(sort, order, limit, offset, filters, lab)


        rows = []
        for result in results:

            project = database.getProjectById(result.id)
            supervisors = project.supervisorsFullNameEng
            studentsMail = [s.email for s in project.students]
            lab = None
            if result.lab:
                lab = database.getLabById(result.lab).acronym
            rows.append({
                "image": f"<img style='width:80px;height:70px;' src='/static/images/projects/{result.image}' alt='{result.image}'" if result.image else "",
                "year": result.year,
                "semester": result.semester,
                "title": result.title,
                "supervisorsNames": ",<br>".join(supervisors),
                "lab": lab,
                "id": result.id,
                "studentsMail": studentsMail
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


def manageProjects():
    if not utils.check_user_lab_admin():
        return redirect(url_for('login'))
    try:
        admin = utils.check_user_admin()
        lab = None if not utils.check_user_lab() else database.getLabByAcronym(flask_login.current_user.userId)
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
        addForm.new_year.choices = [(currentYear, currentYear), (str(int(currentYear) + 1), str(int(currentYear) + 1)),
                                    (str(int(currentYear) + 2), str(int(currentYear) + 2))]
        addForm.new_semester.choices = semesterChoices

        allSupervisors = database.getAllSupervisors()
        supervisorsChoices = [(str(s.id), s.firstNameEng + " " + s.lastNameEng) for s in allSupervisors]
        supervisorsChoices.insert(0, ('', ''))
        addForm.new_supervisor1.choices = supervisorsChoices
        addForm.new_supervisor2.choices = supervisorsChoices
        addForm.new_supervisor3.choices = supervisorsChoices

        editForm.year.choices = [(currentYear, currentYear), (str(int(currentYear) + 1), str(int(currentYear) + 1)),
                                 (str(int(currentYear) + 2), str(int(currentYear) + 2))]
        editForm.semester.choices = semesterChoices
        editForm.supervisor1.choices = supervisorsChoices
        editForm.supervisor2.choices = supervisorsChoices
        editForm.supervisor3.choices = supervisorsChoices

        # get Labs
        allLabs = database.getAllLabs()
        allLabsChoices = [(str(l.id), l.acronym) for l in allLabs]
        editForm.lab.choices = allLabsChoices
        addForm.new_lab.choices = allLabsChoices

        if (request.method == 'POST'):
            formName = request.form['sentFormName']
            if formName == 'editProjectForm':
                project = database.getProjectById(editForm.projectId.data)

                if not project:
                    app.logger.error(
                        'In manageProjects, in editForm, tried to edit a project with id {} that does not exist in the db'.format(
                            editForm.projectId.data))
                    flash("Error: project with id {} is not in the db.".format(editForm.projectId.data), 'danger')
                    return redirect(url_for('manageProjects'))

                app.logger.error("this is the students: {}".format(request.form))
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
                        "image": projectImage,
                        "lab": editForm.lab.data
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
                    app.logger.info(
                        'In manageProjects, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
                    editFormErrorProjectId = editForm.projectId.data
                    if 'csrf_token' in editForm.errors:
                        flash('Error: csrf token expired, please re-send the form.', 'danger')
                    else:
                        flash('There was an error, see details below.', 'danger')
                    if request.form.get('studentsReferrer'):
                        edit_StudentForm = editStudentForm()
                        delete_StudentForm = deleteStudentForm()
                        editFormErrorStudentId = ''

                        return render_template('/admin/students.html', title="Manage Students",
                                               editForm=edit_StudentForm, editProjectForm=editForm, courses=courses,
                                               deleteForm=delete_StudentForm,
                                               editFormErrorStudentId=editFormErrorStudentId,
                                               editProjectErrorId=editFormErrorProjectId)

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
                        "status": "הרשמה",
                        "lab": addForm.new_lab.data
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
        return render_template('/admin/projects.html', title="Manage Projects", courses=courses, addForm=addForm,
                               editForm=editForm, deleteForm=deleteForm, addFormErrors=addFormErrors,
                               editFormErrorProjectId=editFormErrorProjectId, editStudentForm=edit_studentForm,
                               admin=admin, lab=lab)
    except Exception as e:
        app.logger.error('In manageProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
        return redirect(url_for('errorPage'))

def projectStatus(id):
    if not flask_login.current_user.is_authenticated:
        return redirect(url_for('login'))
    if utils.check_user_lab_admin():
        return redirect(url_for('manageProjects'))
    # user is a student
    try:
        student = database.getStudentByStudentId(flask_login.current_user.userId)
        project = None
        isStudentEnrolledInProject = database.isStudentEnrolledInProject(id, student.id)
        if not isStudentEnrolledInProject:
            flash("You are not enrolled in the project.", 'danger')
        else:
            project = database.getProjectById(id)

        return render_template('projectStatus.html', title="Project Status", student=student, project=project,
                               isStudentEnrolledInProject=isStudentEnrolledInProject)
    except Exception as e:
        app.logger.error('In projectStatus, Error is: {}\n{}'.format(e, traceback.format_exc()))
        return redirect(url_for('errorPage'))