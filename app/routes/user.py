from datetime import datetime
from flask import Blueprint, current_app, render_template, session, request, url_for, flash
from werkzeug.utils import redirect
from werkzeug.security import check_password_hash, generate_password_hash
from ..extentions.database import mongo

usermod = Blueprint('usermod',__name__)

@usermod.route('/login', methods=['GET','POST'])
def login():
    if "username" in session:
        return redirect(url_for('langapp.home'))
    elif request.method == 'POST':
        username = request.form.get('usuario')
        password = request.form.get('senha')
        userFound = mongo.db.users.find_one({"username": username})
        if userFound:
            validUser = userFound["username"]
            validName = userFound["name"]
            validPassword = userFound["password"]
            validActive = userFound["passwordActive"]
            validActiveU = userFound["active"]
            
            if validActiveU:
                if check_password_hash(validPassword,password):
                    if validActive:
                        session["username"] = validUser
                        flash(f'Welcome, {validName}','success')
                        current_app.logger.info(f"User {validName} logged in")
                        return redirect(url_for('langapp.home'))
                    else:
                        flash(f'Define a new password, {validName}','warning')
                        return render_template("usuarios/reset.html",user=validUser,menu="Login")

                else:
                    flash("Login failed","danger")
                    current_app.logger.info(f"User {validName} login failed with wrong password")
            else:
                flash('User not active, contact page owner','warning')
                current_app.logger.info(f"User {validName} not active, login failed")
        else:
            flash("Login failed","danger")
            current_app.logger.warn(f"User not found in database")

    return render_template("usuarios/login.html",menu="Login")
    
@usermod.route('/reset', methods=['GET','POST'])
def reset():
    if request.method == 'POST':
        username = request.form.get('usuario')
        password = request.form.get('senha')
        password2 = request.form.get('senha2')
        userFound = mongo.db.users.find_one({"username": username})
        if userFound:
            validUser = userFound["username"]
            validName = userFound["name"]
            validActive = userFound["active"]
            if validActive:
                if (password == password2):
                    mongo.db.users.find_one_and_update({"username": username},{'$set': {"passwordActive": True, "password": generate_password_hash(password)}})
                    session["username"] = validUser
                    flash(f'Success, welcome {validName}','success')
                    return redirect(url_for('langapp.home'))
                else:
                    flash('Passwords do not match','danger')
            else:
                flash('User not active, contact page owner','warning')
                current_app.logger.info(f"User {validName} not active, login failed")

        else:
            flash("User not found",'danger')

    return redirect(url_for("usermod.login"))

@usermod.route('/logout')
def logout():
    session.pop("username",None)
    flash('Logout finished')
    return redirect(url_for('usermod.login'))
