from datetime import datetime, timedelta
import json
import re
import string
import requests
from flask import Blueprint, jsonify, current_app
#from pymongo import collection
from ..extentions.database import mongo
from ..cache import cache
from app.variables import *
from dictionary import Dictionary

backend = Blueprint('backend',__name__)

# Python english dictionary
en_dictionary = Dictionary()

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

# Rate limits
REQUESTS_PER_MINUTE = 60
REQUESTS_PER_HOUR = 1000

@cache.memoize(0)
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
def get_word_api(lang,word):
    """
    API route to look up a word with rate limiting.
    """
    checkCache = cache.get("apiperminute")
    if checkCache:
        if checkCache > REQUESTS_PER_MINUTE:
            current_app.logger.info(f'Too many requests per minute in api')
            return jsonify({"error": "Too many requests. Please try again in a minute."}), 429
        else:
            cache.set("apiperminute",1+checkCache,60)
    else:
        cache.set("apiperminute",1,60)
    checkCache = cache.get("apiperhour")
    if checkCache:
        if checkCache > REQUESTS_PER_HOUR:
            current_app.logger.info(f'Too many requests per hour in api')
            return jsonify({"error": "Too many requests. Please try again in an hour."}), 429
        else:
            cache.set("apiperhour",1+checkCache,3600)
    else:
        cache.set("apiperhour",1,3600)

    data = get_word(lang, word)
    current_app.logger.info(f'Request of word {word} via api')
    return jsonify(data)

@cache.memoize(604800)
def get_word(lang,word):
    if lang == "en":
        current_app.logger.debug(f'Searching word {word} in module dictionary_en')
        data = en_dictionary.lookup(word.lower())
    else:
        data = {"error": f"Language {lang} not available."}
    return {
        'lang': lang,
        'word': word,
        'data': data
    }

def normalize_word(word):
    """
    Normalize a word by converting it to its singular form (for nouns) or infinitive form (for verbs).
    """
    # Handle common plural endings
    if word.endswith("ies"):
        return word[:-3] + "y"  # "cities" → "city"
    elif word.endswith("es"):
        return word[:-2]  # "boxes" → "box"
    elif word.endswith("s"):
        return word[:-1]  # "cats" → "cat"
    # Handle common conjugation
    elif word.endswith("ed"):
        infinitive_word = word[:-2]
        current_app.logger.debug(f'Searching word {infinitive_word} in module dictionary_en')
        if en_dictionary.lookup(infinitive_word):
            return infinitive_word # looked
        if len(infinitive_word) > 2 and infinitive_word[-1] == infinitive_word[-2]:
            infinitive_word = word[:-3]
            current_app.logger.debug(f'Searching word {infinitive_word} in module dictionary_en')
            if en_dictionary.lookup(infinitive_word):
                return infinitive_word # wrapped
        infinitive_word = word[:-1]
        current_app.logger.debug(f'Searching word {infinitive_word} in module dictionary_en')
        if en_dictionary.lookup(infinitive_word):
            return infinitive_word # placed
    elif word.endswith("ing"):
        return word[:-3]
    
    current_app.logger.debug(f'Word could not be normalized, returning {word}')
    return word  # No change

@cache.memoize(30)
def wordIsKnown(word,userdb):
    checkCache = cache.get(word+userdb)
    if checkCache:
        current_app.logger.debug(f'Word {word} was marked in cache as known')
        return True
    else:
        outdb = mongo.db[userdb].find_one({'word': word,'status': 'known'})
        if outdb:
            cache.set(word+userdb,True,600000)
            current_app.logger.debug(f'Word {word} marked in cache as known')
            return True
        else:
            current_app.logger.debug(f'Word {word} not found in database as known')
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
    word_list = re.split(" |'|’|\n|\r|<|>|/|—|…",text)
    for word in word_list:
        newword = word.strip(string.punctuation)
        if not re.match("^[0-9]",newword):
            newword = newword.strip("/|\\<>!?.[]{}“”«»").lower()
            if newword and newword not in wordstotal:

                # Add original word or normalized one
                wordstotal.append(newword)
                wdata = get_word(lang,newword)
                if wdata.get('data'):
                    dataPresent = True
                else:
                    norm_newword = normalize_word(newword)
                    current_app.logger.debug(f'Word {newword} without data, searching normalized word {norm_newword}')
                    nwdata = get_word(lang,norm_newword)
                    if nwdata.get('data'):
                        dataPresent = True
                        current_app.logger.debug(f'Considering normalized word {norm_newword} for word {newword}')
                        newword = norm_newword
                        wdata = nwdata
                    else:
                        dataPresent = False

                # Check if known or learning
                inflashcard = False
                searchWord = True
                if checkbase:
                    if wordIsKnown(newword,basename):
                        wordsknown.append(newword)
                        searchWord = False
                        current_app.logger.debug(f'Word {newword} already marked as known')
                    elif newword in flashcard_list:
                        inflashcard = True

                if searchWord:
                    if dataPresent:
                        try:
                            indexw = word_list.index(word)
                        except:
                            current_app.logger.debug(f'Word {newword} not found in text, phrase empty')
                            phrase = ""
                        else:
                            maxl = len(word_list)
                            if indexw < 10:
                                indexw = 10
                            elif indexw > maxl-11:
                                indexw = maxl-11
                            phrase = ' '.join(word_list[indexw-10:indexw+11])
                        if wordIsKnown(wdata['word'],basename):
                            wordsknown.append(newword)
                            current_app.logger.debug(f'Word {newword} obtained already marked as known')
                        else:
                            if newword != wdata['word']:
                                current_app.logger.debug(f'Setting {newword} as {wdata["word"]}')
                                newword = wdata["word"]
                            if newword not in studylist:
                                wordset.append({
                                    'word': newword,
                                    'dictdata': wdata['data'],
                                    'inflashcard': inflashcard,
                                    'phrase': phrase
                                    })
                                studylist.append(newword)
                                current_app.logger.debug(f'Word {newword} marked to be study')

                                current_app.logger.debug(f'Dictdata {newword}: {wdata["data"]}')
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

def set_last_phrase(word,phrase,userdb):
    outdb = mongo.db[userdb].find_one_and_update({'word': word},{'$set': {'phrase': phrase}})
    if outdb:
        current_app.logger.debug(f'New phrase inserted for word {word}')
    else:
        current_app.logger.error(f'Error inserting new phrase for word {word}')

def set_to_study(word,userdb):
    outdb = mongo.db[userdb].find_one({'word':word})
    if outdb:
        if outdb['status'] != 'learning':
            mongo.db[userdb].find_one_and_update({'word': word},{'$set':{'status': 'learning'}})
    else:
        flashcard = {
            'days': 1,
            'date': datetime.strftime(datetime.now(),"%d/%m/%Y %H:%M")
        }
        mongo.db[userdb].insert_one({'word': word,'status': 'learning','flashcard': flashcard})

def set_to_known(word,userdb):
    outdbv = mongo.db[userdb].find_one({'word':word})
    if outdbv:
        outdb = mongo.db[userdb].find_one_and_update({'word': word},{'$set':{'status': 'known','flashcard': ""}})
    else:
        outdb = mongo.db[userdb].insert_one({'word': word,'status': 'known'})
    if outdb:
        current_app.logger.debug(f'Word {word} in {userdb} updated as known')
        return True
    else:
        current_app.logger.error(f'Error updating {word} in {userdb}')
        return False

def update_fc(word,days,userdb):
    flashcard = {
            'days': days,
            'date': datetime.strftime(datetime.now(),"%d/%m/%Y %H:%M")
    }
    outdb = mongo.db[userdb].find_one_and_update({'word': word, 'status': 'learning'},{'$set': {'flashcard': flashcard}})
    if outdb:
        current_app.logger.debug(f'Word {word} in {userdb} updated with days={days}')
        return True
    else:
        current_app.logger.error(f'Error searching for {word} in {userdb}')
        return False

#datetime.strptime(jogo["Data"],"%d/%m/%Y %H:%M")
#datetime.strftime(datetime.now(),"%d/%m")

@backend.route('/api/flashcard/<userdb>')
@cache.memoize(60)
def get_flashcard(userdb,lang='en'):
    studynow = []
    studyfuture = []
    inflashcard = []
    count_nd = [0,0,0,0]
    now = datetime.now()
    flashdb = [u for u in mongo.db[userdb].find({'status': 'learning'})]
    for i in flashdb:
        i.pop('_id')
        wdate = datetime.strptime(i['flashcard']['date'],"%d/%m/%Y %H:%M")
        limitdate = wdate + timedelta(days=i['flashcard']['days'])
        if now > limitdate:
            i['dictdata'] = get_word(lang,i['word'])['data']
            studynow.append(i)
            count_nd[0] += 1
        else:
            studyfuture.append(i)
            diff = limitdate - now
            if diff.days < 2:
                count_nd[1] += 1
            elif diff.days < 7:
                count_nd[2] += 1
            elif diff.days < 30:
                count_nd[3] += 1

        inflashcard.append(i['word'])
    return {
        'lang': lang,
        'dbname': userdb,
        'langname': LANGNAMES[lang],
        'studynow': studynow,
        'studyfuture': studyfuture,
        'count_now': len(studynow),
        'count_fut': len(studyfuture),
        'inflashcard': inflashcard,
        'counts_nd': count_nd
    }

@backend.route('/api/flashcard/user_fcs/<userid>')
@cache.memoize(60)
def get_user_flashcards(userid):

    dblist = mongo.db.list_collection_names()
    fclist = []
    for lang in SUPPORTED_LANGS:
        langdb = "user" + userid + lang
        if langdb in dblist:
            fclist.append(get_flashcard(langdb,lang))
    return {
        'fclist': fclist,
        'userid': userid
    }

