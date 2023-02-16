from datetime import datetime, time, timedelta
import json
import re
import string
from flask import Blueprint, app, render_template, session, request, url_for, flash, jsonify, current_app
from pymongo import collection
from ..extentions.database import mongo
from ..cache import cache
from wiktionaryparser import WiktionaryParser
from wiktionnaireparser import WiktionnaireParser as wtp

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

@backend.route('/api/<lang>/<word>')
@cache.memoize(600000)
def get_word(lang,word):
    if lang == 'en':
        parser = WiktionaryParser()
        data = parser.fetch(word)
        if data and not data[0]['definitions']:
            data = ""
    elif lang == 'fr':
        page = wtp.from_source(word)
        dictword = {
            'etymology': json.dumps(page.get_etymology()),
            'definitions': []
        }
        data = page.get_parts_of_speech()
    #     for i in speech:
    #         arrtext = []
    #         arrex = []
    #         for k1,t in speech[i].items():
    #             print(t)
    #             #tdic = dict(t)
    #             arrtext.append('string')
    #             if t[0].get('examples'):
    #                 for k2,ex in t['examples'].items():
    #                     #arrex.append(dict(ex)['example'])
    #                     arrex.append('example')
    #         item = {
    #             'partOfSpeech': i,
    #             'text': arrtext,
    #             'translations': {},
    #             'examples': arrex
    #         }
    #         dictword['definitions'].append(item)
    #     data = [dictword]
    else:
        data = ""
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

    for word in text.split():
        if not re.match("^[0-9]",word):
            newword = word.strip(string.punctuation).casefold()
            newword = newword.strip("/|\\<>!?.[]\{\}")
            if newword not in wordstotal:
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
                    wdata = get_word(lang,newword)['data']
                    if wdata:
                        wordset.append({
                            'word': newword,
                            'dictdata': wdata,
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


