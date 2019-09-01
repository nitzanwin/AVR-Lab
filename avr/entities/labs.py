import os
import json
import traceback
import flask_login
from flask import render_template, url_for, flash, redirect, request, jsonify
from avr.forms import addLabForm, editLabForm, deleteLabForm
from avr import database
from avr import utils
from avr import app, db, bcrypt, mail

def manageLabs():
    if not flask_login.current_user.is_authenticated or flask_login.current_user.userType != "admin":
        return redirect(url_for('login'))
    try:
        admin = utils.check_user_admin()
        lab = None if not utils.check_user_lab() else database.getLabByAcronym(flask_login.current_user.userId)
        addForm = addLabForm()
        editForm = editLabForm()
        deleteForm = deleteLabForm()
        addFormErrors = False
        editFormErrorLabId = ''
        if (request.method=='POST'):
            formName = request.form['sentFormName']
            if formName == 'editLabForm':
                lab = database.getLabById(editForm.labId.data)
                if not lab:
                    app.logger.error('In manageLabs, in editForm, tried to edit a lab with id {} that does not exist in the db'.format(editForm.labId.data))
                    flash("Error: Lab with id {} is not in the db.".format(editForm.labId.data), 'danger')
                    return redirect(url_for('manageLabs'))
                if editForm.validate_on_submit():
                    if lab.acronym != editForm.new_acronym.data:
                        labWithAcr = database.getLabByAcronym(editForm.new_acronym.data)
                        if labWithAcr:
                            flash('There is already a lab with the same acronym!', 'danger')
                            return redirect(url_for('editAccount'))
                    projectImage = lab.logo
                    if editForm.new_logo.data:
                        app.logger.info('In manageProjects, in editForm, deleting old project image')
                        utils.delete_logo_image(projectImage) # TODO CHANGE THIS FUNCTIONS
                        projectImage = utils.save_form_image(editForm.new_logo.data, "labs_logo")
                    hashed_password = bcrypt.generate_password_hash(editForm.new_password.data).decode('utf-8')
                    database.updateLab(lab.id,{
                        "name": editForm.new_name.data,
                        "acronym": editForm.new_acronym.data,
                        "password": hashed_password,
                        "description": editForm.description.data,
                        "website": editForm.website.data,
                        "logo": projectImage
                    })
                    flash('Lab was updated successfully!', 'success')
                    return redirect(url_for('manageLabs'))
                else:
                    app.logger.info(
                        'In managelabs, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
                    editFormErrorLabId = editForm.labId.data
                    if 'csrf_token' in editForm.errors:
                        flash('Error: csrf token expired, please re-send the form.', 'danger')
                    else:
                        flash('There was an error, see details below.', 'danger')

            elif formName == 'addLabForm':
                if addForm.validate_on_submit():
                    picFile = None
                    if addForm.logo.data:
                        app.logger.info('In manageLabs, saving image of new lab logo')
                        picFile = utils.save_form_image(addForm.logo.data, "labs_logo")
                    hashed_password = bcrypt.generate_password_hash(addForm.new_password.data).decode('utf-8')
                    newLab = {
                        "name": addForm.new_name.data,
                        "acronym": addForm.new_acronym.data,
                        "password": hashed_password,
                        "description": addForm.description.data,
                        "website": addForm.website.data,
                        "logo": picFile
                    }
                    database.addLab(newLab)

                    flash('Lab was created successfully!', 'success')
                    return redirect(url_for('manageLabs'))
                else:
                    addFormErrors = True
                    app.logger.info('In manageLabs, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
                    if 'csrf_token' in addForm.errors:
                        flash('Error: csrf token expired, please re-send the form.', 'danger')
                    else:
                        flash('There was an error, see details below.', 'danger')

        return render_template('/admin/labs.html', title="Manage Labs", addForm=addForm,
                               editForm=editForm, deleteForm=deleteForm, addFormErrors=addFormErrors,
                               editFormErrorLabId=editFormErrorLabId, admin=admin, lab=lab)
    except Exception as e:
        app.logger.error('In manageLabs, Error is: {}\n{}'.format(e, traceback.format_exc()))
        return redirect(url_for('errorPage'))


def getLabsTableData():
    if not flask_login.current_user.is_authenticated or flask_login.current_user.userType != "admin":
        return redirect(url_for('login'))

    try:
        limit = request.args.get('limit') or 10
        offset = request.args.get('offset') or 0

        totalResults, results = database.getLabsTableData(limit, offset)
        rows = []
        for result in results:
            rows.append({
                "logo": f"<img style='width:80px;height:70px;' src='/static/images/labs_logo/{result.logo}' alt='{result.logo}'" if result.logo else "",
                "name": result.name,
                "acronym": result.acronym,
                "description": result.description,
                "website": f"<a href='{result.website}'>{result.website}</a>",
                "btnEdit": f"<button type='button' onclick='getLabData({result.id})' name='btnEdit' class='btn btn-primary' data-toggle='modal' data-target='#editLabModal'><i class='fa fa-edit fa-fw'></i> Edit</button>",
                "btnDelete": f"<button type='button' onclick='deleteLab({result.id})' name='btnDelete' class='btn btn-danger' data-toggle='modal' data-target='#deleteLabModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
            })

        return jsonify(
            total=totalResults,
            rows=rows
        )

    except Exception as e:
        app.logger.error('In getLabsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
        return jsonify(total=0, rows=[])

def getLabData(id):
    if not flask_login.current_user.is_authenticated or flask_login.current_user.userType != "admin":
         return redirect(url_for('login'))
    try:
        lab = database.getLabById(id)

        labData = {
            "id": lab.id,
            "name": lab.name,
            "acronym": lab.acronym,
            "logo": lab.logo,
            "description": lab.description,
            "password": lab.password,
            "website": lab.website
        }

        return jsonify(labData)

    except Exception as e:
        app.logger.error('In getLabData, error is: {}\n{}'.format(e, traceback.format_exc()))
        return jsonify({})

def deleteLab():
    if not flask_login.current_user.is_authenticated or flask_login.current_user.userType != "admin":
        return redirect(url_for('login'))
    try:
        deleteForm = deleteLabForm()
        lab = database.getLabById(deleteForm.deleteLabId.data)
        if lab:
            app.logger.info('In deleteLab, deleting {}'.format(lab))
            database.deleteLab(lab.id)
            flash('Lab was deleted successfully!', 'primary')
        else:
            app.logger.error(
                'In deleteLab, could not delete lab with id {}, because there is no lab with this id'.format(
                    deleteForm.deleteLabId.data))
            flash("Error: can't delete, lab id {} is not in the db".format(deleteForm.deleteLabId.data),
                  'danger')
        return redirect(url_for('manageLabs'))
    except Exception as e:
        app.logger.error('In deleteLab, Error is: {}'.format(e))
        return redirect(url_for('errorPage'))

def editLab():
    if not utils.check_user_lab():
        return redirect(url_for('login'))
    try:
        admin = utils.check_user_admin()
        lab = None if not utils.check_user_lab() else database.getLabByAcronym(flask_login.current_user.userId)
        form = editLabForm()

        if request.method == 'POST':
            if form.validate_on_submit():
                if lab.acronym != form.new_acronym.data:
                    labWithAcr = database.getLabByAcronym(form.new_acronym.data)
                    if labWithAcr:
                        flash('There is already a lab with the same acronym!', 'danger')
                        return redirect(url_for('editLab'))
                projectImage = lab.logo
                if form.new_logo.data:
                    app.logger.info('In manageProjects, in editForm, deleting old project image')
                    utils.delete_logo_image(projectImage)  # TODO CHANGE THIS FUNCTIONS
                    projectImage = utils.save_form_image(form.new_logo.data, "labs_logo")
                hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
                database.updateLab(lab.id, {
                    "name": form.new_name.data,
                    "acronym": form.new_acronym.data,
                    "password": hashed_password,
                    "description": form.description.data,
                    "website": form.website.data,
                    "logo": projectImage
                })
                flash('Lab was updated successfully!', 'success')
                return redirect(url_for('home'))
            else:
                app.logger.info('In Edit Account, form is NOT valid. form.errors:{}'.format(form.errors))
                if 'csrf_token' in form.errors:
                    flash('Error: csrf token expired, please re-enter your credentials.', 'danger')
                else:
                    flash('There was an error, see details below.', 'danger')
        elif request.method == 'GET':
            form.labId.data = lab.id
            form.new_name.data = lab.name
            form.new_acronym.data = lab.acronym
            form.new_password.data = lab.password
            form.new_logo.data = lab.logo
            form.website.data = lab.website
            form.description.data = lab.description
        return render_template('/admin/editLab.html', title="Edit Lab", form=form, admin=admin, lab=lab)
    except Exception as e:
        app.logger.error('In editAccount, Error is: {}\n{}'.format(e, traceback.format_exc()))
        return redirect(url_for('errorPage'))