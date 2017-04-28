import json
import pickle
from secrets import token_urlsafe

import telebot
from django.template.smartif import key
from flask import Flask, request
from flask.ext.redis import FlaskRedis

from telebot.types import Update

from model import Test, Unit, Draft

bot = telebot.TeleBot('345467048:AAEFochiYcGcP7TD5JqYwco8E56cOYCydrk')

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
        temp['key'] = Draft(token, Test(token), None)

        bot.send_message(message.chat.id, f'Your token: {token}')
        msg = bot.send_message(message.chat.id, 'Set the questions count:')
        bot.register_next_step_handler(msg, set_units_num)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


def set_units_num(message):
    try:
        temp['key'].num = int(message.text)
        msg = bot.send_message(message.chat.id, 'Set the question text:')
        bot.register_next_step_handler(msg, set_unit_text)
    except Exception as e:
        bot.reply_to(message, str(e) + '1')


def set_unit_text(message):
    try:
        test = temp['key'].test
        test.units.append(Unit(message.text, None))

        msg = bot.send_message(message.chat.id, 'Set the question answer:')
        bot.register_next_step_handler(msg, set_units_answer)
    except Exception as e:
        bot.reply_to(message, str(e) + '2')


def set_units_answer(message):
    try:
        draft = temp['key']
        test = draft.test
        num = draft.num
        test.units[-1].answer = message.text

        if num > 1:
            temp['key'].num = num - 1
            msg = bot.send_message(message.chat.id, 'Set the question text:')
            bot.register_next_step_handler(msg, set_unit_text)
        else:
            del temp['key']
            redis[draft.token] = pickle.dumps(test)
            bot.send_message(message.chat.id, 'Test successfully created!')
            li = []
            for u in test.units:
                li.append(f'{u.text} {u.answer}')

            bot.send_message(message.chat.id, str(li))

    except Exception as e:
        bot.reply_to(message, str(e) + '3')


@bot.message_handler(commands=['test'])
def start_test(message):
    try:
        msg = bot.send_message(message.chat.id, 'Enter the token')
        bot.register_next_step_handler(msg, input_token)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


def input_token(message):
    try:
        temp['key'] = redis[message.text]
        msg = bot.send_message(message.chat.id, 'Set the question text:')
        bot.register_next_step_handler(msg, set_unit_text)
    except Exception as e:
        bot.reply_to(message, str(e) + '1')


def get_task(message):
    try:
        test = temp['key']
        test.results['key'] = 0
        test.count = len(test.units)
        msg = bot.send_message(message.chat.id, test.units[0].text)
        bot.register_next_step_handler(msg, set_unit_text)
    except Exception as e:
        bot.reply_to(message, str(e) + '1')


def check_answer(message):
    try:
        key = message.from_user.username
        test = temp['key']
        units = test.units
        test.num = len(units)
        answer = units.pop(0).answer
        test.results['key'] += answer == message.text
        if units:
            bot.register_next_step_handler(message, set_unit_text)
        else:
            del temp['key']
            redis.set('', pickle.dumps(test))
            bot.send_message(message.chat.id, f'Your result is: {test.results[key]}/{test.num}')
    except Exception as e:
        bot.reply_to(message, str(e) + '3')


@bot.message_handler(commands=['res'])
def input_key_res(message):
    try:
        msg = bot.send_message(message.chat.id, 'Enter the key')
        bot.register_next_step_handler(msg, get_result)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


@bot.message_handler(commands=['res'])
def get_result(message):
    try:
        key = message.from_user.username
        test = temp['key']
        bot.send_message(message.chat.id, f'Your result is: {test.results[key]}/{len(test.units)}')
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


@app.route("/update", methods=['POST'])
def get_message():
    bot.process_new_updates([Update.de_json(request.stream.read().decode("utf-8"))])
    return '', 200


@app.route("/")
def webhook():
    redis.flushdb()
    bot.remove_webhook()
    bot.set_webhook(url="https://teststackbot.herokuapp.com/update")
    return '', 200


if __name__ == '__main__':
    app.run()
