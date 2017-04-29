import json
import pickle
from secrets import token_urlsafe

import telebot
from django.template.smartif import key
from flask import Flask, request
from flask.ext.redis import FlaskRedis

from telebot.types import Update

from model import Test, Task, Draft

bot = telebot.TeleBot('345467048:AAEFochiYcGcP7TD5JqYwco8E56cOYCydrk')

app = Flask(__name__)
app.config['REDIS_URL'] = 'redis://h:p0c08b0fb92a7de45ea5db298baf96d2f7bd48981912d73a19ec96ae3b2eb4634' \
                          '@ec2-34-251-82-220.eu-west-1.compute.amazonaws.com:7559'
redis = FlaskRedis(app)
tests = {}


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = '/new - create new test' \
           '/pass - pass the test' \
           '/mres - my result of the test' \
           '/res - all results of the test'
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['new'])
def new_test(message):
    try:
        test = Test()
        test.key = token_urlsafe(8)
        tests['key'] = test

        bot.send_message(message.chat.id, f'Your key: {test.key}')
        msg = bot.send_message(message.chat.id, 'Enter number of tasks')
        bot.register_next_step_handler(msg, set_tasks_num)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


def set_tasks_num(message):
    try:
        tests['key'].num = int(message.text)
        msg = bot.send_message(message.chat.id, 'Enter the task text')
        bot.register_next_step_handler(msg, set_task_text)
    except Exception as e:
        bot.reply_to(message, str(e) + '1')


def set_task_text(message):
    try:
        task = Task()
        task.text = message.text
        tests['key'].tasks.append(task)
        msg = bot.send_message(message.chat.id, 'Enter the task correct answer')
        bot.register_next_step_handler(msg, set_task_answer)
    except Exception as e:
        bot.reply_to(message, str(e) + '2')


def set_task_answer(message):
    try:
        test = tests['key']
        test.tasks[-1].answer = message.text

        if test.num > 1:
            test.num -= 1
            msg = bot.send_message(message.chat.id, 'Enter number of tasks')
            bot.register_next_step_handler(msg, set_task_text)
        else:
            del tests['key']
            redis[test.key] = pickle.dumps(test)
            bot.send_message(message.chat.id, 'Test successfully created!')
            li = []
            for u in test.tasks:
                li.append(f'{u.text} {u.answer}')

            bot.send_message(message.chat.id, str(li))
    except Exception as e:
        bot.reply_to(message, str(e) + '3')


@bot.message_handler(commands=['pass'])
def begin(message):
    try:
        msg = bot.send_message(message.chat.id, 'Enter the key')
        bot.register_next_step_handler(msg, get_test)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


def get_test(message):
    try:
        tests['key'] = redis[message.text]
        num = len(tests['key'].tasks)
        msg = bot.send_message(message.chat.id, f'Let\'s start the test, number of tasks: {num}')
        bot.register_next_step_handler(msg, set_unit_text)
    except Exception as e:
        bot.reply_to(message, str(e) + '1')


def get_task(message):
    try:
        test = tests['key']
        test.results['key'] = 0
        msg = bot.send_message(message.chat.id, 'Enter your answer')
        msg = bot.send_message(message.chat.id, test.tasks[0].text)
        bot.register_next_step_handler(msg, set_unit_text)
    except Exception as e:
        bot.reply_to(message, str(e) + '1')


def check_answer(message):
    try:
        key = message.from_user.username
        test = tests['key']
        tasks = test.tasks
        test.num = len(tasks)
        answer = tasks.pop(0).answer
        test.results['key'] += answer == message.text
        if tasks:
            bot.register_next_step_handler(message, set_unit_text)
        else:
            del tests['key']
            redis.set('', pickle.dumps(test))
            bot.send_message(message.chat.id, f'Your result is: {test.results[key]}/{test.num}')
    except Exception as e:
        bot.reply_to(message, str(e) + '3')


@bot.message_handler(commands=['res'])
def input_key_result(message):
    try:
        msg = bot.send_message(message.chat.id, 'Enter the key')
        bot.register_next_step_handler(msg, get_result)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


@bot.message_handler(commands=['res'])
def get_result(message):
    try:
        test = tests['key']
        result = test.results[message.from_user.username]
        num = len(test.tasks)
        bot.send_message(message.chat.id, f'Your result is: {result} / {num}')
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


@bot.message_handler(commands=['res'])
def input_key_results(message):
    try:
        msg = bot.send_message(message.chat.id, 'Enter the key:')
        bot.register_next_step_handler(msg, get_result)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


@bot.message_handler(commands=['res'])
def get_results(message):
    try:
        test = tests['key']
        num = len(test.tasks)
        results = test.results.items()
        bot.send_message(message.chat.id, 'Results:\n'.join(f'{r[0]}: {r[1]} / {num}\n' for r in results))
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
