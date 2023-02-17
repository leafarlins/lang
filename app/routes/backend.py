from datetime import datetime, time, timedelta
import json
import re
import string
import requests
from flask import Blueprint, app, render_template, session, request, url_for, flash, jsonify, current_app
from pymongo import collection
from ..extentions.database import mongo
from ..cache import cache
from wiktionaryparser import WiktionaryParser

backend = Blueprint('backend',__name__)

#@cache.memoize(300)

#https://github.com/Suyash458/WiktionaryParser
#https://github.com/Surkal/WiktionnaireParser

# mongodb of each user
# {
# 'word': palavra,
# 'status': 'known'/'learning'
# 'flashcard': {
#   'days': 5,
#   'mult': 1.5
#   'date': dateformat
# }}

def wordExists(lang,word):
    current_app.logger.debug(f'Check if word {word} exists in {lang}')
    url = 'https://'+lang+'.wiktionary.org/w/api.php?action=query&titles='+word+'&format=json'
    outurl = requests.get(url)
    outj = json.loads(outurl.text)
    current_app.logger.debug(f'Response: {outurl.text}')
    data = ""
    if outj.get('query'):
        for i in outj['query']['pages']:
            if int(i) > 0:
                data = [{
                    'definitions': [],
                    'link': 'https://'+lang+'.wiktionary.org/wiki/'+word
                }]
    # Check if the casefold word exists
    if not data and word[0].isupper():
        casefold = wordExists(lang,word.casefold())
        if casefold['data']:
            return casefold
    return {
        'word': word,
        'data': data
    }


@backend.route('/api/<lang>/<word>')
@cache.memoize(600000)
def get_word(lang,word):
    if lang in ['en','fr']:
        outwe = wordExists(lang,word)
        word = outwe['word']
        data = outwe['data']   
    else:
        data = ""
    if lang == 'en':
        parser = WiktionaryParser()
        dataparser = parser.fetch(word)
        if dataparser and not dataparser[0]['definitions']:
            data = outwe['data']
        else:
            data = dataparser
            data[0]['link'] = outwe['data'][0].get('link')
    return {
        'lang': lang,
        'word': word,
        'data': data
    }

def wordIsKnown(word,userdb):
    checkCache = cache.get(word+userdb)
    if checkCache:
        return True
    else:
        outdb = mongo.db[userdb].find_one({'word': word,'status': 'known'})
        if outdb:
            cache.set(word+userdb,True,600000)
            return True
        else:
            return False

@backend.route('/api/text/<lang>/<text>')
@cache.memoize(300)
def get_text(lang,text,userid=""):
    wordset = []
    wordsnot = []
    wordstotal = []
    wordsknown = []
    studylist = []
    basename = ""
    if userid != "":
        basename = 'user' + str(userid) + lang
        checkbase = True
        flashcard_list = get_flashcard(basename)['inflashcard']
        current_app.logger.debug(f'Using database {basename} for user')
    else:
        checkbase = False
    word_list = re.split(" |'|’|\n",text)
    for word in word_list:
        if not re.match("^[0-9]",word):
            newword = word.strip(string.punctuation)
            newword = newword.strip("/|\\<>!?.[]\{\}")
            if newword and newword not in wordstotal:
                wordstotal.append(newword)
                inflashcard = False
                # Check if known or learning
                searchWord = True
                if checkbase:
                    if wordIsKnown(newword,basename):
                        wordsknown.append(newword)
                        searchWord = False
                        current_app.logger.debug(f'Word {newword} already marked as known')
                    elif newword in flashcard_list:
                        inflashcard = True
                if searchWord:
                    wdata = get_word(lang,newword)
                    if wdata.get('data'):
                        if newword != wdata['word']:
                            current_app.logger.debug(f'Setting {newword} as {wdata["word"]}')
                            newword = wdata["word"]
                        wordset.append({
                            'word': newword,
                            'dictdata': wdata['data'],
                            'inflashcard': inflashcard
                            })
                        studylist.append(newword)
                        current_app.logger.debug(f'Word {newword} marked to be study')
                    else:
                        wordsnot.append(newword)
                        current_app.logger.debug(f'Word {newword} marked as not found')
    return {
        'lang': lang,
        'wordstudy': sorted(wordset, key= lambda k: k['word']),
        'wordstudylist': sorted(studylist),
        'wordsnot': sorted(wordsnot),
        'wordtotal': sorted(wordstotal),
        'wordsknown': sorted(wordsknown),
        'count_total': len(wordstotal),
        'count_dict': len(studylist),
        'count_known': len(wordsknown),
        'count_notf': len(wordsnot),
        'check_db': checkbase,
        'userdb': basename
    }

def set_to_study(word,userdb):
    outdb = mongo.db[userdb].find_one({'word':word})
    if outdb:
        if outdb['status'] != 'learning':
            mongo.db[userdb].find_one_and_update({'word': word},{'$set':{'status': 'learning'}})
    else:
        flashcard = {
            'days': 1,
            'mult': 1.5,
            'date': datetime.strftime(datetime.now(),"%d/%m/%Y %H:%M")
        }
        mongo.db[userdb].insert_one({'word': word,'status': 'learning','flashcard': flashcard})

def set_to_known(word,userdb):
    outdb = mongo.db[userdb].find_one({'word':word})
    if outdb:
        mongo.db[userdb].find_one_and_update({'word': word},{'$set':{'status': 'known','flashcard': ""}})
    else:
        mongo.db[userdb].insert_one({'word': word,'status': 'known'})

#datetime.strptime(jogo["Data"],"%d/%m/%Y %H:%M")
#datetime.strftime(datetime.now(),"%d/%m")

@backend.route('/api/flashcard/<userdb>')
@cache.memoize(600)
def get_flashcard(userdb):
    lang = 'en'
    studynow = []
    studyfuture = []
    inflashcard = []
    flashdb = [u for u in mongo.db[userdb].find({'status': 'learning'})]
    for i in flashdb:
        i.pop('_id')
        wdate = datetime.strptime(i['flashcard']['date'],"%d/%m/%Y %H:%M")
        limitdate = wdate + timedelta(days=i['flashcard']['days'])
        if datetime.now() > limitdate:
            i['dictdata'] = get_word(lang,i['word'])['data']
            studynow.append(i)
        else:
            studyfuture.append(i)
        inflashcard.append(i['word'])
    return {
        'studynow': studynow,
        'studyfuture': studyfuture,
        'count_now': len(studynow),
        'count_fut': len(studyfuture),
        'inflashcard': inflashcard
    }


