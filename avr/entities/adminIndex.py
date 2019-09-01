import os
import json
import traceback
from flask import render_template, url_for, flash, redirect, request, jsonify
import flask_login
from avr.forms import adminMailForm
from avr import database, utils
from avr import app, db, bcrypt, mail
from flask_mail import Message

def adminMail():
    if not utils.check_user_lab_admin():
        return redirect(url_for('home'))
    try:
        admin = utils.check_user_admin()
        lab = None if not utils.check_user_lab() else database.getLabByAcronym(flask_login.current_user.userId)
        form = adminMailForm()
        if request.method == "POST":
            if form.validate_on_submit():
                recipients = form.email.data.split(',')
                title = form.title.data
                content = form.content.data
                emailWasSent = sendMail(recipients,title,content)
                # emailWasSent = False
                if emailWasSent:
                    app.logger.info('Email was sent successfully')
                    flash('The email was sent successfully.', 'info')
                    return redirect(url_for('adminMail'))
            else:
                app.logger.info('In resetRequest, form is NOT valid. form.errors:{}'.format(form.errors))
                flash('There was an error, see details below.', 'danger')
        return render_template('/admin/adminMail.html', title="Mail", form=form, admin=admin, lab=lab)
    except Exception as e:
        app.logger.error('In resetRequest, Error is: {}\n{}'.format(e, traceback.format_exc()))
        return redirect(url_for('errorPage'))

def sendMail(recipients,title,content):
    msg = Message(title, sender='noreply@technion.ac.il', recipients=recipients)
    msg.body = content
    try:
        mail.send(msg)
        return True
    except Exception as e:
        flash('Error: could not send mail', 'danger')
        app.logger.error('In sendResetEmail, could not send mail to {}. Error is: {}\n{}'.format(recipients, e,
                                                                                                 traceback.format_exc()))
        return False