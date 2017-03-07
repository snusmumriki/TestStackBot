from secrets import token_urlsafe

import telebot
from flask import Flask, request
from flask.ext.redis import FlaskRedis
from flask.json import dumps, loads

from telebot.types import Update

from model import Test, Unit

bot = telebot.TeleBot('306447523:AAG4NEunw0OezXDbDjtTZMEFmRnLwYO5Yn8')

app = Flask(__name__)
app.config['REDIS_URL'] = 'redis://h:p0c08b0fb92a7de45ea5db298baf96d2f7bd48981912d73a19ec96ae3b2eb4634@ec2-34-251-82' \
                          '-220.eu-west-1.compute.amazonaws.com:7559'
redis = FlaskRedis(app)
temp = {}


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = '''/new - create new test
    /test - start test'''
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['new'])
def new_test(message):
    try:
        token = token_urlsafe(8)
        redis.set(token, dumps(Test(token)))
        temp['token'] = token

        msg = bot.send_message(message.chat.id, 'Set the questions count:')
        bot.register_next_step_handler(msg, set_units_num)
    except Exception as e:
        bot.reply_to(message, str(e))


def set_units_num(message):
    try:
        temp['num'] = int(message.text)
        msg = bot.send_message(message.chat.id, 'Set the question text:')
        bot.register_next_step_handler(msg, set_unit_text)
    except Exception as e:
        bot.reply_to(message, str(e))


def set_unit_text(message):
    try:
        token = temp['token']
        test = loads(redis.get(token))
        unit = Unit()
        unit.text = message.text
        test.units.append(unit)
        redis.set(token, dumps(test))

        msg = bot.send_message(message.chat.id, 'Set the question answer:')
        bot.register_next_step_handler(msg, set_units_answer)

    except Exception as e:
        bot.reply_to(message, str(e))


def set_units_answer(message):
    try:
        token = temp['token']
        num = temp['num']

        test = loads(redis.get(token))
        test.units[-1].answer = message.text
        redis.set(token, dumps(test))

        if num > 1:
            msg = bot.send_message(message.chat.id, 'Set the question text:')
            temp['num'] = num - 1
            bot.register_next_step_handler(msg, set_unit_text)
        else:
            del temp['num']
            del temp['token']

    except Exception as e:
        bot.reply_to(message, str(e))


@bot.message_handler(commands=['test'])
def start(message):
    bot.reply_to(message, 'Hello, ')


@app.route("/update", methods=['POST'])
def get_message():
    bot.process_new_updates([Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://teststackbot.herokuapp.com/update")
    return '!', 200


if __name__ == '__main__':
    app.run()
