import json
import requests
import boto3
from botocore.exceptions import ClientError
import os
import click
import pymongo
from pymongo.collection import ReturnDocument
from ..extentions.database import mongo
from flask import Blueprint

emailCommands = Blueprint('email',__name__)

MONGO_URI = os.getenv('MONGO_URI')

# Replace sender@example.com with your "From" address.
# This address must be verified with Amazon SES.
SENDER = "LangApp <lang@leafarlins.com>"
REPLYTO = ["leafarlins@gmail.com"]

# Replace recipient@example.com with a "To" address. If your account 
# is still in the sandbox, this address must be verified.
#RECIPIENT = "recipient@example.com"

# Specify a configuration set. If you do not want to use a configuration
# set, comment the following variable, and the 
# ConfigurationSetName=CONFIGURATION_SET argument below.
#CONFIGURATION_SET = "ConfigSet"

# If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
AWS_REGION = "us-east-1"

# The subject line for the email.
SUBJECT = "Amazon SES Test (SDK for Python)"

# The character encoding for the email.
CHARSET = "UTF-8"

# Create a new SES resource and specify a region.
client = boto3.client('ses',region_name=AWS_REGION)
#client = boto3.client('ses',region_name=AWS_REGION,verify=False)


def send_email(RECIPIENT,SUBJECT,BODY_TEXT,BODY_HTML):

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            ReplyToAddresses=REPLYTO,
            # If you are not using a configuration set, comment or delete the
            # following line
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

@emailCommands.cli.command("testEmail")
@click.argument("recipient")
@click.argument("subject")
def test_email(recipient,subject):
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Amazon SES Test (Python)\r\n"
                "This email was sent with Amazon SES using the "
                "AWS SDK for Python (Boto)."
                )
                
    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
    <h1>Amazon SES Test (SDK for Python)</h1>
    <p>This email was sent with
        <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
        <a href='https://aws.amazon.com/sdk-for-python/'>
        AWS SDK for Python (Boto)</a>.</p>
    </body>
    </html>
                """
    send_email(recipient,subject,BODY_TEXT,BODY_HTML)

#@emailCommands.cli.command("send_reset_email")
#@click.argument("username")
#@click.argument("password")
#@click.argument("test",required=False)
def send_adduser_email(username,password,test=False):
    subject="Usuário criado"
    corpo_html="<h1 style=\"text-align: center\">Langapp - New user</h1><p>Your user were created. Access the site with your temporary password.</p>"
    corpo_html+="<p>User: "+username+"</p>"
    corpo_html+="<p>Password: "+password+"</p><p>Langapp: <a href=\"https://langapp.leafarlins.com\">langapp.leafarlins.com</a></p>"
    corpo_text = "User: "+username+"\Password: "+password
    BODY_HTML = """<html>
    <head></head>
    <body style=\"font-family: \"Trebuchet MS\", Arial, Helvetica, sans-serif;\">
    """ + corpo_html + """
    </body>
    </html>
                """
    BODY_TEXT = (corpo_text)

    if test:
        recipient = "leafarlins@gmail.com"
    else:
        recipient = username
    send_email(recipient,subject,BODY_TEXT,BODY_HTML)

def send_reset_email(username,password,test=False):
    subject="Reset de senha"
    corpo_html="<h1 style=\"text-align: center\">Reset de Senha</h1><p>Sua senha foi resetada. Acesse com a senha temporária.</p>"
    corpo_html+="<p>Usuário: "+username+"</p>"
    corpo_html+="<p>Senha: "+password+"</p>"
    corpo_text = "Senha resetada.\nUsuário: "+username+"\nSenha: "+password
    BODY_HTML = """<html>
    <head></head>
    <body style=\"font-family: \"Trebuchet MS\", Arial, Helvetica, sans-serif;\">
    """ + corpo_html + """
    </body>
    </html>
                """
    BODY_TEXT = (corpo_text)

    if test:
        recipient = "leafarlins@gmail.com"
    else:
        recipient = username
    send_email(recipient,subject,BODY_TEXT,BODY_HTML)

@emailCommands.cli.command("send_aviso")
@click.argument("aviso")
def send_aviso(aviso):
    subject="Warning"
    corpo_text = "Warning:\n"
    corpo_html="<h1 style=\"text-align: center\">Warning</h1><p style=\"text-align: center\">"
    corpo_text += aviso
    corpo_html += aviso
    BODY_HTML = """<html>
    <head></head>
    <body style=\"font-family: \"Trebuchet MS\", Arial, Helvetica, sans-serif;\">
    """ + corpo_html + """
    </body>
    </html>
                """
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = (corpo_text)
    #print(corpo_html)
    print(corpo_text)
    user_list = [ u for u in mongo.db.users.find({"active": True})]
    for user in user_list:
        print(f'Enviando email para usuário { user["username"] }')
        recipient = user["username"]
        #send_email(recipient,subject,BODY_TEXT,BODY_HTML)
    # Para testes:
    #send_email("leafarlins@gmail.com",subject,BODY_TEXT,BODY_HTML)
