from flask import Blueprint, current_app, render_template, session, request, url_for, flash
import pymongo
from werkzeug.utils import redirect
from werkzeug.security import check_password_hash
from ..extentions.database import mongo
from ..cache import cache

langapp = Blueprint('langapp',__name__)

@langapp.route('/', methods=['GET','POST'])
def home():
    return render_template("home.html",menu="Home")

@langapp.route('/about')
def about():
    return render_template("about.html",menu="About")