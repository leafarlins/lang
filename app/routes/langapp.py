import json
from flask import Blueprint, current_app, make_response, render_template, session, request, url_for, flash
import pymongo
from werkzeug.utils import redirect
from werkzeug.security import check_password_hash
from pwgen import pwgen
from app.routes.backend import get_text, set_to_known, set_to_study
from ..extentions.database import mongo
from ..cache import cache

langapp = Blueprint('langapp',__name__)

#app.logger.debug('This is a DEBUG message')
#app.logger.info('This is an INFO message')
#app.logger.warning('This is a WARNING message')
#app.logger.error('This is an ERROR message')

@langapp.route('/')
def home():
    return render_template("home.html",menu="Home")

@langapp.route('/text', methods=['GET','POST'])
def textstudy():
    if request.method == 'POST':
        textreceived = request.values.get("texto")
        if textreceived:
            if "username" in session:
                userdb = mongo.db.users.find_one({'username': session["username"]})
                if userdb:
                    textobj = get_text('en',textreceived,userdb.get('uid'))
                else:
                    flash(f'Error getting username database','danger')
                    return redirect(url_for('langapp.home'))
            else:
                textobj = get_text('en',textreceived)
            randomstore = pwgen(16, symbols=False)
            cache.set(randomstore,json.dumps(textobj),3600*48)
            resp = make_response(render_template("text.html",menu="Words",words=textobj,currentword=0))
            resp.set_cookie('textdata',randomstore)
            resp.set_cookie('currentw','0')
            return resp
        else:
            flash(f'Null text received','danger')
            return redirect(url_for('langapp.home'))
    else:
        data = request.cookies.get('textdata')
        jsondata = ""
        if data:
            cachedata = cache.get(data)
            if cachedata:
                jsondata = json.loads(cachedata)
            currentword = request.cookies.get('currentw')
        if jsondata:
            return render_template("text.html",menu="Words",words=jsondata,currentword=int(currentword))
        else:
            flash(f'Paste a text to study','warning')
            return redirect(url_for('langapp.home'))

@langapp.route('/text/action',methods=['POST'])
def nextword():
    action = request.values.get("submit")
    if action:
        if action in ['nextword','study','know']:
            currentword = request.cookies.get('currentw')
            nextw = int(currentword) + 1
            data = request.cookies.get('textdata')
            jsondata = ""
            if data:
                cachedata = cache.get(data)
                if cachedata:
                    jsondata = json.loads(cachedata)
            if jsondata:
                if action == 'study':
                    set_to_study(jsondata['wordstudy'][int(currentword)]['word'],jsondata['userdb'])
                elif action == 'know':
                    set_to_known(jsondata['wordstudy'][int(currentword)]['word'],jsondata['userdb'])
                resp = make_response(render_template("text.html",menu="Words",words=jsondata,currentword=nextw))
                resp.set_cookie('currentw',str(nextw))
                return resp
            else:
                flash(f'Data not found','danger')
        else:
            flash(f'Action {action} not valid','danger')
            current_app.logger.error(f"Action {action} not valid in form")
    else:
        flash(f'Action empty','danger')
        current_app.logger.error(f"Action empty")
    
    return redirect(url_for('langapp.home'))

@langapp.route('/flashcard', methods=['GET','POST'])
def flashcard():
    cards = []
    resp = make_response(render_template("flashcard.html",menu="Flashcard",cards=cards))
    return resp



    



@langapp.route('/about')
def about():
    return render_template("about.html",menu="About")