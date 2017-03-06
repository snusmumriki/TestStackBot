from secrets import token_bytes

import telebot
import os
from flask import Flask, request
from flask.ext.redis import FlaskRedis

from model import Test, Unit

bot = telebot.TeleBot('306447523:AAG4NEunw0OezXDbDjtTZMEFmRnLwYO5Yn8')

app = Flask(__name__)
app.config[
    'REDIS_URL'] = 'redis://h:p0c08b0fb92a7de45ea5db298baf96d2f7bd48981912d73a19ec96ae3b2eb4634@ec2-34-251-82-220.eu-west-1.compute.amazonaws.com:7559'
redis = FlaskRedis(app)

test = None
b = False


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = '''/new - create new test
    /test - start test'''
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['new'])
def start(message):
    b = True
    token = token_bytes(16)
    test = Test(token, [])
    unit = Unit()
    while b:
        bot.send_message(message.chat.id, 'Set the question text:')
        unit.text = yield
        bot.send_message(message.chat.id, 'Set the question type:')
        unit.type = yield
        bot.send_message(message.chat.id, 'Set the question answer:')
        test.units.append(unit)


@bot.message_handler(commands=['create'])
def start(message):
    b = False


@bot.message_handler(commands=['test'])
def start(message):
    bot.reply_to(message, 'Hello, ' + message.from_user.first_name)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)


@app.route("/update", methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://teststackbot.herokuapp.com/update")
    redis.set('foo', 'bar')
    return redis.get('foo'), 200


if __name__ == '__main__':
    app.run()
