import traceback
import flask_login
from flask import render_template, url_for, flash, redirect, request, jsonify
from avr.forms import addSupervisorForm, editSupervisorForm, deleteSupervisorForm
from avr import database
from avr import utils
from avr import app

def manageSupervisors():
    if not utils.check_user_lab_admin():
        return redirect(url_for('login'))
    try:
        admin = utils.check_user_admin()
        lab = None if not utils.check_user_lab() else database.getLabByAcronym(flask_login.current_user.userId)
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
        return render_template('/admin/supervisors.html', title="Manage Supervisors", editForm=editForm, deleteForm=deleteForm,
                               addForm=addForm, editFormErrorSupervisorId=editFormErrorSupervisorId, addFormErrors=addFormErrors,
                               admin=admin, lab=lab)
    except Exception as e:
        app.logger.error('In manageSupervisors, Error is: {}\n{}'.format(e, traceback.format_exc()))
        return redirect(url_for('errorPage'))


def getSupervisorsTableData():
    if not utils.check_user_lab_admin():
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
        status = [{"value": "", "text": "ALL"}, {"value": "active", "text": "active"},
                  {"value": "not active", "text": "not active"}]

        return jsonify(
            total=totalResults,
            rows=rows,
            filterOptions={
                "status": status
            })

    except Exception as e:
        app.logger.error('In getSupervisorsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
        return jsonify(total=0, rows=[])

def getSupervisorData(id):
    if not utils.check_user_lab_admin():
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

def deleteSupervisor():
    if not utils.check_user_lab_admin():
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