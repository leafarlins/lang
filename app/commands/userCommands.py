import click
import getpass
from pwgen import pwgen

from app.commands.email import send_adduser_email, send_reset_email
from ..extentions.database import mongo
from werkzeug.security import generate_password_hash
from flask import Blueprint

userCommands = Blueprint('user',__name__)

@userCommands.cli.command("getUser")
@click.argument("name")
def get_user(name):
    userCollection = mongo.db.users
    user = [u for u in userCollection.find({"name": name})]
    print(user)

@userCommands.cli.command("addUser")
@click.argument("username")
@click.argument("name")
def create_user(username,name):
    mongoconfig = mongo.db.settings.find_one_and_update({"config": "userid"},{'$inc': {'userid':1}})
    if mongoconfig:
        userid = mongoconfig['userid']
    else:
        mongo.db.settings.insert_one({'config':'userid','userid': 0})
        userid = 0

    userExists = mongo.db.users.find_one({"username": username})
    if userExists:
        print(f'User {username} exists')
    else:
        password = pwgen(10, symbols=False)
        user = {
            "username": username,
            "name": name,
            "uid": userid,
            "password": generate_password_hash(password),
            "active": True,
            "passwordActive": False
        }
        outdb = mongo.db.users.insert_one(user)
        print('Usuário cadastrado com sucesso')
        print(f'Usuário: {username}')
        print(f'Senha temporária: {password}')
        print("Enviando email...")
        send_adduser_email(username,password)

@userCommands.cli.command("resetPassword")
@click.argument("username")
@click.argument("test",required=False)
def reset_password(username,test=False):
    userCollection = mongo.db.users
    password = pwgen(10, symbols=False)
    #password = getpass.getpass()

    userExists = userCollection.find_one({"username": username})
    if userExists:
        userCollection.find_one_and_update({'username': username},{'$set': {"passwordActive": False, "password": generate_password_hash(password)}})
        print(f'Usuário: {username}')
        print(f'Senha temporária: {password}')
        #if userExists["sendEmail"]:
        print("Enviando email de reset...")
        #send_reset_email(username,password,test)
    else:
        print("Usuário não encontrado.")

@userCommands.cli.command("listUsers")
def list_users():
    lista_users = [u for u in mongo.db.users.find()]
    ativos = ""
    inativos = ""
    gokopa = ""
    pagos = ""
    sendemail = ""
    for u in lista_users:
        if u["active"]:
            ativos += " " + u["name"]
        else:
            inativos += " " + u["name"]
    print(f'Lista de users active ativos:{ativos}')
    print(f'Lista de users active inativos:{inativos}')

@userCommands.cli.command("activeUser")
@click.argument("user")
@click.argument("tipo")
@click.argument("status")
def list_users(user,tipo,status):
    if status == "true":
        atividade = True
    elif status == "false":
        atividade = False
    else:
        print("Informe true ou false para status.")
        return
    userCollection = mongo.db.users
    userExists = userCollection.find_one({"name": user})
    if userExists:
        userCollection.find_one_and_update({'name': user},{'$set': {tipo: atividade}})
        print("Usuário",user,"setado para status",tipo,"=",atividade)
    else:
        print("Usuário não encontrado.")


@userCommands.cli.command("dropUser")
@click.argument("username")
def delete_user(username):
    userCollection = mongo.db.users
    userExists = userCollection.find_one({"username": username})
    if userExists:
        question = input(f'Deseja deletar o usuário {username}? (S/N) ')
        if question.upper() == "S":
            userCollection.delete_one({"username": username})
            print("Usuário deletado com sucesso!")
        else:
            exit()
    else:
        print("Usuário não encontrado.")



