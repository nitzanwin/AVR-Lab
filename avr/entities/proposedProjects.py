import os
import json
import traceback
import flask_login
from flask import render_template, url_for, flash, redirect, request, jsonify
from avr.forms import addProposedProjectForm, editProposedProjectForm, deleteProposedProjectForm, searchProposedProjects
from avr import database
from avr import utils
from avr import app, db, bcrypt, mail


def manageProposedProjects():
    if not utils.check_user_lab_admin():
        return redirect(url_for('login'))
    try:
        admin = utils.check_user_admin()
        lab = None if not utils.check_user_lab() else database.getLabByAcronym(flask_login.current_user.userId)
        addForm = addProposedProjectForm()
        editForm = editProposedProjectForm()
        deleteForm = deleteProposedProjectForm()
        addFormErrors = False
        editFormErrorProposedProjectId = ''

        # get supervisors
        allSupervisors = database.getAllSupervisors()
        activeSupervisors = database.getActiveSupervisors()
        allSupervisorsChoices = [(str(s.id), s.firstNameEng + " " + s.lastNameEng) for s in allSupervisors]
        activeSupervisorsChoices = [(str(s.id), s.firstNameEng + " " + s.lastNameEng) for s in activeSupervisors]
        allSupervisorsChoices.insert(0, ('', ''))
        activeSupervisorsChoices.insert(0, ('', ''))

        editForm.supervisor1.choices = allSupervisorsChoices
        editForm.supervisor2.choices = allSupervisorsChoices
        editForm.supervisor3.choices = allSupervisorsChoices

        addForm.newSupervisor1.choices = activeSupervisorsChoices
        addForm.newSupervisor2.choices = activeSupervisorsChoices
        addForm.newSupervisor3.choices = activeSupervisorsChoices

        # get Labs
        allLabs = database.getAllLabs()
        allLabsChoices = [(str(l.id), l.acronym) for l in allLabs]
        editForm.lab.choices = allLabsChoices
        addForm.newLab.choices = allLabsChoices

        if (request.method == 'POST'):
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
                        "lab": addForm.newLab.data,
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
                    app.logger.info(
                        'In manageProposedProjects, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
                    if 'csrf_token' in addForm.errors:
                        flash('Error: csrf token expired, please re-send the form.', 'danger')
                    else:
                        flash('There was an error, see details below.', 'danger')
                    addFormErrors = True
            elif formName == 'editProposedProjectForm':
                proposedProject = database.getProposedProjectById(editForm.proposedProjectId.data)

                if not proposedProject:
                    app.logger.error(
                        'In manageProposedProjects, in editForm, tried to edit a proposed project with id {} that does not exist in the db'.format(
                            editForm.proposedProjectId.data))
                    flash("Error: project with id {} is not in the db.".format(editForm.proposedProjectId.data),
                          'danger')
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
                        "image": picFile,
                        "lab": editForm.lab.data
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
                    app.logger.info(
                        'In manageProposedProjects, editForm is NOT valid. editForm.errors:{}'.format(editForm.errors))
                    if 'csrf_token' in editForm.errors:
                        flash('Error: csrf token expired, please re-send the form.', 'danger')
                    else:
                        flash('There was an error, see details below.', 'danger')
                    editFormErrorProposedProjectId = editForm.proposedProjectId.data

        return render_template('/admin/proposedProjects.html', title="Manage Proposed Projects", addForm=addForm,
                               editForm=editForm, deleteForm=deleteForm, addFormErrors=addFormErrors,
                               editFormErrorProposedProjectId=editFormErrorProposedProjectId,
                               admin=admin, lab=lab)
    except Exception as e:
        app.logger.error('In manageProposedProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
        return redirect(url_for('errorPage'))


def getProposedProjectData(id):
    if not utils.check_user_lab_admin():
        return redirect(url_for('login'))

    try:
        proposedProject = database.getProposedProjectById(id)
        supervisors = [{"id": s.id, "fullNameEng": s.firstNameEng + " " + s.lastNameEng} for s in
                       proposedProject.supervisors]

        proposedProjectData = {
            "id": proposedProject.id,
            "image": proposedProject.image,
            "title": proposedProject.title,
            "description": proposedProject.description,
            "lab": proposedProject.lab,
            "supervisors": supervisors
        }

        return jsonify(proposedProjectData)

    except Exception as e:
        app.logger.error('In getProposedProjectData, error is: {}\n{}'.format(e, traceback.format_exc()))
        return jsonify({})


def deleteProposedProjects():
    if not utils.check_user_lab_admin():
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
            app.logger.info(
                'In deleteProposedProjects, could not delete proposed project with id {}, because there is no proposed project with this id'.format(
                    deleteForm.deleteProposedProjectId.data))
            flash("Error: can't delete, proposed project id is not in the db", 'danger')
        return redirect(url_for('manageProposedProjects'))
    except Exception as e:
        app.logger.error('In deleteProposedProjects, Error is: {}'.format(e))
        return redirect(url_for('errorPage'))


def getProposedProjectsTableData():
    if not utils.check_user_lab_admin():
        return redirect(url_for('login'))

    try:
        sort = request.args.get('sort')
        order = request.args.get('order') or "desc"
        limit = request.args.get('limit') or 10
        offset = request.args.get('offset') or 0
        filters = request.args.get('filter')
        lab = None if utils.check_user_admin() else database.getLabByAcronym(flask_login.current_user.userId).id
        totalResults, results = database.getProposedProjectsTableData(sort, order, limit, offset, filters, lab)

        rows = []
        for result in results:
            supervisors = database.getProposedProjectById(result.id).supervisorsFullNameEng
            lab = None
            if result.lab:
                lab = database.getLabById(result.lab).acronym
            rows.append({
                "image": f"<img style='width:80px;height:70px;' src='/static/images/proposed_projects/{result.image}' alt='{result.image}'" if result.image else "",
                "title": result.title,
                "description": result.description,
                "lab": lab,
                "supervisorsNames": ",<br>".join(supervisors),
                "btnEdit": f"<button type='button' onclick='getProposedProjectData({result.id})' name='btnEdit' class='btn btn-primary' data-toggle='modal' data-target='#editProposedProjectModal'><i class='fa fa-edit fa-fw'></i> Edit</button>",
                "btnDelete": f"<button type='button' onclick='deleteProposedProject({result.id})' name='btnDelete' class='btn btn-danger' data-toggle='modal' data-target='#deleteProposedProjectModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
            })

        return jsonify(
            total=totalResults,
            rows=rows,
            filterOptions={
                "lab": database.getLabFilter()
            }
        )

    except Exception as e:
        app.logger.error('In getProposedProjectsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
        return jsonify(total=0, rows=[])

def showProposedProjects():
    try:
        student = None
        admin = None
        if flask_login.current_user.is_authenticated:
            if flask_login.current_user.userType == "student":
                student = database.getStudentByStudentId(flask_login.current_user.userId)
            elif flask_login.current_user.userType == "admin":
                admin = database.getAdminByAdminId(flask_login.current_user.userId)
        lab = None if not utils.check_user_lab() else database.getLabByAcronym(flask_login.current_user.userId)

        search_form = searchProposedProjects()
        # get Labs
        allLabs = database.getAllLabs()
        allLabsChoices = [(str(l.id), l.acronym) for l in allLabs]
        search_form.lab.choices = [('', 'ALL')] + allLabsChoices


        filters = {}
        if request.method == 'GET':
            app.logger.error('GET')
            search_form.lab.data = request.args.get('lab', None)
            search_form.search_text.data = request.args.get('search_text', None)
            filters = {
                'lab': request.args.get('lab', None),
                'search': request.args.get('search_text', None)
            }
        app.logger.info('\nIn proposedProjects, filters are: {}\n'.format(filters))
        proposedProjects = database.getAllProposedProjects(filters)
        return render_template('proposedProjects.html', title="Proposed Projects", search_form=search_form,
                               proposedProjects=proposedProjects, student=student, admin=admin, lab=lab)
    except Exception as e:
        app.logger.error('In proposedProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
        return redirect(url_for('errorPage'))
