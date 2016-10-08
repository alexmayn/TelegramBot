# -*- coding: utf-8 -*-
"""
  Based on pyTelegramBotyAPI
  GitHub: https://github.com/eternnoir/pyTelegramBotAPI
  documentation: https://pypi.python.org/pypi/pyTelegramBotAPI/0.3.6
  deploeing: https://retifrav.github.io/blog/2015/10/24/telegram-bot/
             https://kondra007.gitbooks.io/telegram-bot-lessons/content/multiple_bots_1.html

"""

import config
import time
from datetime import datetime, timedelta
import telebot
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


filePath = os.path.join(config.MESSAGES_FOLDER, config.FILE_NAME)

server = smtplib.SMTP('smtp.gmail.com:587')
server.ehlo()
server.set_debuglevel(1)

bot = telebot.TeleBot(config.token)

messagesToSend = []
# getMe
user = bot.get_me()
print(user)

# getUpdates
updates = bot.get_updates(1234, 100, 20) #get_Updates(offset, limit, timeout):
print(updates)



# Run smtp server
server.starttls()
server.login(config.username, config.password)

start = datetime.now()

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
    server.sendmail(config.fromaddr, config.toaddr, msg.as_string().encode('ascii'))

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

        '''
          Send all messages afte timer is finished
        '''
        if datetime.now() >= start + timedelta(seconds=config.TIMEOUT):
            sendMessages()
            os.remove(filePath)
            start = datetime.now()


if __name__ == '__main__':
     bot.polling(none_stop=True, interval=0)

