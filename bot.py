#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  Based on pyTelegramBotyAPI
  GitHub: https://github.com/eternnoir/pyTelegramBotAPI
  documentation: https://pypi.python.org/pypi/pyTelegramBotAPI/0.3.6
  deploeing: https://retifrav.github.io/blog/2015/10/24/telegram-bot/
             https://kondra007.gitbooks.io/telegram-bot-lessons/content/multiple_bots_1.html

"""

import cherrypy
import telebot
import logging
import config
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

#config = config_local

API_TOKEN = config.token

WEBHOOK_HOST = config.webHookHost # '<ip/host where the bot is running>'
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_TOKEN)


filePath = os.path.join(config.MESSAGES_FOLDER, config.FILE_NAME)
print(filePath)

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN)
start = datetime.utcnow()

def sendMessages():
    '''
    Load all messages from file? read and send to e-mail
    :param message:
    :return:
    '''
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.set_debuglevel(1)

    # Run smtp server
    server.starttls()
    server.login(config.username, config.password)

    messagesToSend = []
    with open(filePath, mode='r', encoding="utf8") as messgeFile:
         for line in messgeFile:
             messagesToSend.append(line)

    messagesToSend = ''.join(messagesToSend)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = config.subj
    msg["From"] = config.fromaddr
    msg["To"] = config.toaddr
    text = "".join(messagesToSend)
    part1 = MIMEText(text.encode("utf-8"), "plain", "utf-8")
    msg.attach(part1)
    logger.info('Trying send message to e-mail')
    try:
        server.sendmail(config.fromaddr, config.toaddr, msg.as_string().encode('ascii'))
        logger.info('Send succcess!')
    finally:
        server.close()


# WebhookServer, process webhook calls
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
           'content-type' in cherrypy.request.headers and \
           cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message,
                 ("Hi there, I am a bot Tihik.\n"
                  "I am here to provide you messages from Church groups."))


@bot.message_handler(content_types=['document', 'audio'])
def handle_docs_audio(message):
    """
    This func can be get media data from thred and send it by e-mail
    """
    pass


# Handle all other messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    global start
    logger.info('message was response %s' % (message.text))
    # This is filter by group Id
    if message.text and (message.chat.id == config.MINIST_GROUP_CHAT_ID or message.chat.id == config.BOT_CHAT_ID):
        logger.info('start performing...')
        if message.from_user.first_name != None:
            authorName = message.from_user.first_name
        else:
            authorName = ''

        if message.from_user.last_name != None:
            authorName = '{0} {1}'.format(authorName, message.from_user.last_name)
        else:
            authorName
        messageTime = datetime.fromtimestamp(int(message.date)).strftime('%Y-%m-%d  %H:%M:%S')
        text = "\nDate: {0} - {1}: \n {2}".format(messageTime, authorName, message.text)

        '''
         Save all messages to file
        '''
        with open(filePath, mode='a', encoding="utf8") as messgeFile:
            messgeFile.write(text)
            messgeFile.close()
            logger.info('Added message: {}'.format(text))
            logger.info('Time to send: {}, Send time {}, timedelta: {}'.format((start + timedelta(seconds=config.TIMEOUT))-datetime.utcnow(),
                                                                                start + timedelta(seconds=config.TIMEOUT), timedelta(seconds=config.TIMEOUT)))

        '''
          Send all messages after timer is finished
        '''
        if datetime.utcnow() >=  start + timedelta(seconds=config.TIMEOUT):
            sendMessages()
            os.remove(filePath)
            start = datetime.utcfromtimestamp(message.date)


# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Start cherrypy server
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})

