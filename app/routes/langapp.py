import json
from flask import Blueprint, current_app, make_response, render_template, session, request, url_for, flash
import pymongo
from werkzeug.utils import redirect
from werkzeug.security import check_password_hash
from pwgen import pwgen
from app.routes.backend import get_text, get_user_flashcards, set_to_known, set_to_study, get_flashcard, update_fc
from ..extentions.database import mongo
from ..cache import cache
from app.variables import *

langapp = Blueprint('langapp',__name__)

#app.logger.debug('This is a DEBUG message')
#app.logger.info('This is an INFO message')
#app.logger.warning('This is a WARNING message')
#app.logger.error('This is an ERROR message')

@langapp.route('/')
def home():
    cook = request.cookies.get("preflang")
    if cook not in SUPPORTED_LANGS:
        cook = 'en'
    return render_template("home.html",menu="Home",preflang=cook)

@langapp.route('/text', methods=['GET','POST'])
def textstudy():
    if request.method == 'POST':
        textreceived = request.values.get("texto")
        lang = request.values.get("btnradio")
        if lang not in SUPPORTED_LANGS:
            lang = 'en'
        if textreceived:
            if "username" in session:
                userdb = mongo.db.users.find_one({'username': session["username"]})
                if userdb:
                    textobj = get_text(lang,textreceived,userdb.get('uid'))
                else:
                    flash(f'Error getting username database','danger')
                    return redirect(url_for('langapp.home'))
            else:
                textobj = get_text(lang,textreceived)
            randomstore = pwgen(16, symbols=False)
            cache.set(randomstore,json.dumps(textobj),3600*48)
            resp = make_response(render_template("text.html",menu="Words",words=textobj,currentword=0))
            resp.set_cookie('textdata',randomstore)
            resp.set_cookie('currentw','0')
            resp.set_cookie('preflang',lang)
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
                if action == 'study' and not jsondata['wordstudy'][int(currentword)]['inflashcard']:
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

@cache.cached(timeout=20)
@langapp.route('/flashcard', methods=['GET','POST'])
def flashcard():
    fclist = []
    if 'username' in session:
        userdb = mongo.db.users.find_one({'username': session["username"]})
        if userdb:
            fclist = get_user_flashcards(str(userdb.get('uid')))
        else:
            flash(f'Error getting username database','danger')
    resp = make_response(render_template("flashcard.html",menu="Flashcard",fclist=fclist))
    return resp

@langapp.route('/flashcard/study', methods=['POST'])
def study_flashcard():
    if 'username' in session:
        action = request.values.get("submit")
        if action == 'start':
            dbname = request.values.get("database")
            langdb = request.values.get("fclang")
            fc = get_flashcard(dbname,langdb)
            randomstore = dbname + pwgen(8, symbols=False)
            cache.set(randomstore,json.dumps(fc),3600*48)
            resp = make_response(render_template("fcstudy.html",menu="Flashcard",fc=fc,currentfcw=0))
            resp.set_cookie('fcdata',randomstore)
            resp.set_cookie('currentfcw','0')
            return resp
        elif action in ['easy','medium','hard','know']:
            storeid = request.cookies.get('fcdata')
            jsondata = ""
            currentfcw = 0
            if storeid:
                fcdata = cache.get(storeid)
                if fcdata:
                    jsondata = json.loads(fcdata)
                    currentfcw = int(request.cookies.get('currentfcw'))
                    newfc = currentfcw+1
            if jsondata:
                resp = make_response(render_template("fcstudy.html",menu="Flashcard",fc=jsondata,currentfcw=newfc))
                resp.set_cookie('currentfcw',str(newfc))
                if action == 'know':
                    outdb = set_to_known(jsondata['studynow'][currentfcw]['word'],jsondata['dbname'])
                else:
                    multiplier = MULT_FC[action]
                    new_days = jsondata['studynow'][currentfcw]['flashcard']['days'] * multiplier
                    if action == 'hard' and new_days > MULT_FC['max_hard']:
                        new_days = MULT_FC['max_hard']
                    elif new_days > MULT_FC['max_days']:
                        new_days = MULT_FC['max_days']
                        word = jsondata['studynow'][currentfcw]['word']
                        flash(f'Word {word} reached max days, consider setting as known next time','info')
                    outdb = update_fc(jsondata['studynow'][currentfcw]['word'],new_days,jsondata['dbname'])
                if outdb:
                    return resp
                else:
                    flash(f'Error updating database','danger')
            else:
                flash(f'Data not found, choose a flashcard to study','warning')
        else:
            flash(f'Choose a flashcard to study','warning')
    else:
        flash(f'User should be logged in','danger')
    return redirect(url_for('langapp.flashcard'))

@cache.cached(timeout=3600)
@langapp.route('/about')
def about():
    return render_template("about.html",menu="About")