import os
import pickle
from secrets import token_urlsafe

import telebot
from flask import Flask, request
from redis import from_url

from telebot.types import Update, ReplyKeyboardMarkup, KeyboardButton


class Task:
    is_text = True
    text = None
    correct = None


class Test:
    tasks = []
    results = {}


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
        test.num = int(message.text.split()[-1])
        tests['key'] = test
        bot.send_message(message.chat.id, f'Your key: {test.key}')
        msg = bot.send_message(message.chat.id, 'Enter the task text')
        bot.register_next_step_handler(msg, set_task_text)
    except Exception as e:
        bot.reply_to(message, str(e) + ' 0')


def set_task_text(message):
    try:
        task = Task()
        task.text = message.text
        bot.send_message(message.chat.id, str(message.content_type))
        '''task.is_text = message.content_type == 'photo'
        if task.is_text:
            task.text = message.text
            
        else:
            task.text = message.photo'''
        tests['key'].tasks.append(task)
        msg = bot.send_message(message.chat.id, 'Enter the task correct answer')
        bot.register_next_step_handler(msg, set_task_correct_answer)
        '''markup = ReplyKeyboardMarkup(one_time_keyboard=True, row_width=4)
        markup.row(KeyboardButton(a) for a in answer)'''
    except Exception as e:
        bot.reply_to(message, str(e) + ' 2')


def set_task_correct_answer(message):
    try:
        test = tests['key']
        answer = message.text
        if answer[0] == ':':
            answer = set(answer.split()[1:])
        test.tasks[-1].correct = answer

        if test.num > 1:
            test.num -= 1
            msg = bot.send_message(message.chat.id, 'Enter the task text')
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
        bot.reply_to(message, str(e) + ' 3')


@bot.message_handler(commands=['pass'])
def get_test(message):
    try:
        key = message.text.split()[-1]
        test = pickle.loads(redis[key])
        test.key = message.text
        test.num = len(test.tasks)
        test.ctasks = test.tasks.copy()
        tests['key'] = test
        test.results[message.from_user.username] = 0
        bot.send_message(message.chat.id, f'Let\'s start the test, number of tasks: {test.num}')

        task = test.tasks[0]
        if task.is_text:
            msg = bot.send_message(message.chat.id, task.text)
        else:
            msg = bot.send_photo(message.chat.id, task.text)
        bot.register_next_step_handler(msg, get_task)
    except Exception as e:
        bot.reply_to(message, str(e) + ' 1')


def get_task(message):
    try:
        test = tests['key']
        tasks = test.ctasks
        name = message.from_user.username
        correct = tasks.pop(0).correct
        if correct is set:
            answer = set(message.text.split())
        else:
            answer = message.text
        test.results[name] += answer == correct
        if tasks:
            msg = bot.send_message(message.chat.id, tasks[0].text)
            bot.register_next_step_handler(msg, get_task)
        else:
            bot.send_message(message.chat.id, f'Your result is: {test.results[name]} / {test.num}')
            key = test.key
            del test.key
            del test.num
            del test.ctasks
            del tests['key']
            redis[key] = pickle.dumps(test)
    except Exception as e:
        bot.reply_to(message, str(e) + '3')


@bot.message_handler(commands=['mres'])
def get_result(message):
    try:
        test = pickle.loads(redis[message.text.split()[-1]])
        result = test.results[message.from_user.username]
        num = len(test.tasks)
        bot.send_message(message.chat.id, f'Your result is: {result} / {num}')
    except Exception as e:
        bot.reply_to(message, str(e) + '1')


@bot.message_handler(commands=['res'])
def get_list_results(message):
    try:
        test = pickle.loads(redis[message.text.split()[-1]])
        num = len(test.tasks)
        items = test.results.items()
        if num:
            bot.send_message(message.chat.id, 'Results:\n' + ''.join(f'{i[0]}: {i[1]} / {num}\n' for i in items))
        else:
            bot.send_message(message.chat.id, 'No results')
    except Exception as e:
        bot.reply_to(message, str(e) + '1')


@bot.message_handler(commands=['del'])
def delete_test(message):
    try:
        bot.send_message(message.chat.id, 'Test successfully deleted!')
    except Exception as e:
        bot.reply_to(message, str(e) + '1')


@app.route('/update', methods=['POST'])
def update():
    bot.process_new_updates([Update.de_json(request.stream.read().decode('utf-8'))])
    return '', 200


@app.route('/')
def index():
    redis.flushdb()
    bot.remove_webhook()
    bot.set_webhook(url='https://teststackbot.herokuapp.com/update')
    return '', 200


if __name__ == '__main__':
    app.run()
