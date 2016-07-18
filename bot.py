# -*- coding: utf-8 -*-
import config
import telebot
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


fromaddr = 'Mr. Robot <aam@niipp.ru>'

toaddr = 'Administrator <aam@niipp.ru>'

subj = 'Notification from system'

username = 'my@email.com'

password = 'my_password'

server = smtplib.SMTP('smtp.gmail.com:587')

server.set_debuglevel(1);


bot = telebot.TeleBot(config.token)

server.starttls()
server.login(username, password)

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    bot.send_message(message.chat.id, 'This is my response for you!')

    if message.text:

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subj

        msg["From"] = fromaddr
        msg["To"] = toaddr

        part1 = MIMEText(message.text.encode("utf-8"), "plain", "utf-8")
        msg.attach(part1)

        server.sendmail(fromaddr, toaddr, msg.as_string().encode('ascii')) #

        bot.send_message(message.chat.id, 'Sended to e-mail')

if __name__ == '__main__':
     bot.polling(none_stop=True)

