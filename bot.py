# -*- coding: utf-8 -*-
"""
  Based on pyTelegramBotyAPI
  GitHub: https://github.com/eternnoir/pyTelegramBotAPI
  documentation: https://pypi.python.org/pypi/pyTelegramBotAPI/0.3.6
  deploeing: https://retifrav.github.io/blog/2015/10/24/telegram-bot/
             https://kondra007.gitbooks.io/telegram-bot-lessons/content/multiple_bots_1.html

"""

import config_local
import cherrypy
import time
from datetime import datetime, timedelta
import telebot
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import logging

config = config_local

WEBHOOK_HOST = 'IP_Address'
WEBHOOK_PORT = 443
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)



logger = logging.basicConfig(filename='bot.log', level=logging.DEBUG)

config = config_local
filePath = os.path.join(config.MESSAGES_FOLDER, config.FILE_NAME)

server = smtplib.SMTP('smtp.gmail.com:587')
server.ehlo()
server.set_debuglevel(1)

bot = telebot.TeleBot(config.token)

messagesToSend = []
# getMe
#user = bot.get_me()
#logging.info('User {}'.format(user))

# getUpdates
#updates = bot.get_updates(1234, 100, 20) #get_Updates(offset, limit, timeout):
#logging.info('Updates: {}'.format(updates))


start = datetime.now()

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


#TODO: remove it
def listener(messages):
    for m in messages:
        print(str(m))


def sendMessages():
    '''
    Load all messages from file? read and send to e-mail
    :param message:
    :return:
    '''
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
    logging.info('Trying send message to e-mail')
    try:
        server.sendmail(config.fromaddr, config.toaddr, msg.as_string().encode('ascii'))

    finally:
        server.close()

@bot.message_handler(content_types=['document', 'audio'])
def handle_docs_audio(message):
    """
    This func can be get media data from thred and send it by e-mail
    """
    pass

@bot.message_handler(func=lambda m: True, content_types=['text'])
def repeat_all_messages(message):
    global messagesToSend
    global timeout
    global start

    # This is filter by group Id
    if message.text and (message.chat.id == config.MINIST_GROUP_CHAT_ID or message.chat.id == config.BOT_CHAT_ID):
        if message.from_user.first_name != None:
            authorName = message.from_user.first_name
        else:
            authorName = ''

        if message.from_user.last_name != None:
            authorName = '{0} {1}'.format(authorName, message.from_user.last_name)
        else:
            authorName
        #messageTime = message.date #datetime.fromtimestamp(message.date).strftime('%Y %m %d  %H:%M:%S')
        text = "\n{0} - {1}: \n {2}".format('Date:', authorName, message.text)

        '''
         Save all messages to file
        '''
        with open(filePath, mode='a', encoding="utf8") as messgeFile:
            messgeFile.write(text)
            messgeFile.close()
            logging.info('Added message: {}'.format(text))
            logging.info('Time to send: {}'.format((start + timedelta(seconds=config.TIMEOUT))-datetime.now()))

        '''
          Send all messages after timer is finished
        '''
        if datetime.now() >= start + timedelta(seconds=config.TIMEOUT):
            sendMessages()
            os.remove(filePath)
            start = datetime.now()


#if __name__ == '__main__':
#     bot.polling(none_stop=True)

bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})


