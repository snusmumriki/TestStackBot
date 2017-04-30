import os
import pickle
from secrets import token_urlsafe

import telebot
from flask import Flask, request
from redis import from_url

from telebot.types import Update

from model import Test, Task

bot = telebot.TeleBot('345467048:AAEFochiYcGcP7TD5JqYwco8E56cOYCydrk')

app = Flask(__name__)
redis = from_url(os.environ['REDIS_URL'])
tests = {}


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text = '/new - create new test\n' \
           '/pass - pass the test\n' \
           '/mres - my result of the test\n' \
           '/res - all results of the test\n' \
           '/del - delete the test\n'
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
            key = test.key
            del test.key
            del test.num
            del tests['key']
            redis[key] = pickle.dumps(test)
            bot.send_message(message.chat.id, 'Test successfully created!')
            bot.send_message(message.chat.id, str(pickle.dumps(test)))
    except Exception as e:
        bot.reply_to(message, str(e) + '    3')


@bot.message_handler(commands=['pass'])
def get_test_hint(message):
    try:
        msg = bot.send_message(message.chat.id, 'Enter the key')
        bot.register_next_step_handler(msg, get_test)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


def get_test(message):
    try:
        test = pickle.loads(redis[message.text])
        test.key = message.text
        test.num = len(test.tasks)
        tests['key'] = test
        test.results[message.from_user.username] = 0
        bot.send_message(message.chat.id, f'Let\'s start the test, number of tasks: {test.num}')

        msg = bot.send_message(message.chat.id, test.tasks[0].text)
        bot.register_next_step_handler(msg, get_task)
    except Exception as e:
        bot.reply_to(message, str(e) + ' 1')


def get_task(message):
    try:
        test = tests['key']
        tasks = test.tasks
        answer = tasks.pop(0).answer
        name = message.from_user.username
        test.results[name] += answer == message.text
        if tasks:
            msg = bot.send_message(message.chat.id, test.tasks[0].text)
            bot.register_next_step_handler(msg, get_task)
        else:
            bot.send_message(message.chat.id, f'Your result is: {test.results[name]}/{test.num}')
            key = test.key
            del test.key
            del test.num
            del tests['key']
            redis[key] = pickle.dumps(test)
    except Exception as e:
        bot.reply_to(message, str(e) + '3')


@bot.message_handler(commands=['res'])
def get_result_hint(message):
    try:
        msg = bot.send_message(message.chat.id, 'Enter test the key')
        bot.register_next_step_handler(msg, get_result)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


@bot.message_handler(commands=['res'])
def get_result(message):
    try:
        test = pickle.loads(redis[message.text])
        result = test.results[message.from_user.username]
        num = len(test.tasks)
        bot.send_message(message.chat.id, f'Your result is: {result} / {num}')
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


@bot.message_handler(commands=['res'])
def get_list_results_hint(message):
    try:
        msg = bot.send_message(message.chat.id, 'Enter the test key:')
        bot.register_next_step_handler(msg, get_list_results)
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


@bot.message_handler(commands=['res'])
def get_list_results(message):
    try:
        test = pickle.loads(redis[message.text])
        num = len(test.tasks)
        items = test.results.items()
        bot.send_message(message.chat.id, 'Results:\n'.join(f'{i[0]}: {i[1]} / {num}\n' for i in items))
    except Exception as e:
        bot.reply_to(message, str(e) + '0')


@app.route('/update', methods=['POST'])
def get_message():
    bot.process_new_updates([Update.de_json(request.stream.read().decode('utf-8'))])
    return '', 200


@app.route('/')
def webhook():
    redis.flushdb()
    bot.remove_webhook()
    bot.set_webhook(url='https://teststackbot.herokuapp.com/update')
    return '', 200


if __name__ == '__main__':
    app.run()
