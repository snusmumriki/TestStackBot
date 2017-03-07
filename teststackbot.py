from secrets import token_urlsafe

import telebot
from flask import Flask, request
from flask.ext.redis import FlaskRedis
from telebot.types import Update

from model import Test, Unit

bot = telebot.TeleBot('306447523:AAG4NEunw0OezXDbDjtTZMEFmRnLwYO5Yn8')

app = Flask(__name__)
app.config['REDIS_URL'] = 'redis://h:p0c08b0fb92a7de45ea5db298baf96d2f7bd48981912d73a19ec96ae3b2eb4634@ec2-34-251-82' \
                          '-220.eu-west-1.compute.amazonaws.com:7559'
redis = FlaskRedis(app)


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = '''/new - create new test
    /test - start test'''
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['new'])
def new_test(message):
    token = token_urlsafe(16)
    redis.set(token, Test(token, []))
    msg = bot.send_message(message.chat.id, 'Set the questions count:')
    msg.token = token
    bot.register_next_step_handler(msg, set_units_num)


def set_units_num(message):
    msg = bot.send_message(message.chat.id, 'Set the question text:')
    msg.token = message.token
    msg.num = int(message.text)
    bot.register_next_step_handler(msg, set_unit_text)


def set_unit_text(message):
    test = redis.get(message.token)
    unit = Unit()
    unit.text = message.text
    test.units.append(unit)
    redis.set(message.token, test)

    msg = bot.send_message(message.chat.id, 'Set the question answer:')
    msg.token = message.token
    msg.num = message.num
    bot.register_next_step_handler(msg, set_units_answer)


def set_units_answer(message):
    test = redis.get(message.token)
    test.units[-1].answer = message.text
    redis.set(message.token, test)
    if message.num > 1:
        msg = bot.send_message(message.chat.id, 'Set the question text:')
        msg.num = message.num - 1
        bot.register_next_step_handler(msg, set_unit_text)


@bot.message_handler(commands=['test'])
def start(message):
    bot.reply_to(message, 'Hello, ' + message.from_user.first_name)


'''@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)'''


@app.route("/update", methods=['POST'])
def get_message():
    bot.process_new_updates([Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://teststackbot.herokuapp.com/update")
    redis.set('foo', 'bar')
    return redis.get('foo'), 200


if __name__ == '__main__':
    app.run()
