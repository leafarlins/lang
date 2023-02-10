from datetime import datetime, time
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

@backend.route('/api/<lang>/<word>')
@cache.memoize(300)
def get_word(lang,word):
    if lang == 'en':
        parser = WiktionaryParser()
        data = parser.fetch(word)
        if data and not data[0]['definitions']:
            data = ""
    elif lang == 'fr':
        page = wtp.from_source(word)
        dictword = {
            'etymology': page.get_etymology(),
            'definitions': []
        }
        speech = page.get_parts_of_speech()
        for i in speech:
            arrtext = []
            arrex = []
            for k1,t in speech[i].items():
                print(t)
                #tdic = dict(t)
                arrtext.append('string')
                if t[0].get('examples'):
                    for k2,ex in t['examples'].items():
                        #arrex.append(dict(ex)['example'])
                        arrex.append('example')
            item = {
                'partOfSpeech': i,
                'text': arrtext,
                'translations': {},
                'examples': arrex
            }
            dictword['definitions'].append(item)
        data = [dictword]
    else:
        data = ""
    return {
        'lang': lang,
        'word': word,
        'data': data
    }

@backend.route('/api/text/<lang>/<text>')
@cache.memoize(300)
def get_text(lang,text):
    wordset = []
    wordsnot = []
    wordstotal = []
    wordsknown = []
    words_in_dict = 0
    for word in text.split():
        if not re.match("^[0-9]",word):
            newword = word.strip(string.punctuation).casefold()
            if newword not in wordstotal:
                wordstotal.append(newword)
                wdata = get_word(lang,newword)['data']
                if wdata:
                    words_in_dict += 1
                    wordset.append({
                        'word': newword,
                        'dictdata': wdata
                        })
                else:
                    wordsnot.append(newword)
    return {
        'lang': lang,
        'wordstudy': sorted(wordset, key= lambda k: k['word']),
        'wordsnot': sorted(wordsnot),
        'wordtotal': sorted(wordstotal),
        'wordsknown': sorted(wordsknown),
        'count_total': len(wordstotal),
        'count_dict': words_in_dict
    }
