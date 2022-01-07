import telebot
import os
import codecs

from functools import wraps
from telebot import types
from jinja2 import Template
from dotenv import load_dotenv
from flask import Flask, request
from services.order_service import OrderService


load_dotenv()

# bot initialization
TOKEN = os.getenv('API_BOT_TOKEN')
SERVER_URL = os.getenv('SERVER_URL')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_steps = {}
order_service = OrderService()

commands = {
    'start': 'Start using this bot',
    'order': 'Please, write an Order Id',
    'help': 'Useful information about this bot',
    'contacts': 'Developer contacts',
}


def get_user_step(uid):
    if uid not in user_steps:
        user_steps[uid] = 0
    return user_steps[uid]


# decorator for bot actions
def send_action(action):
    """Sends 'action' while processing func command."""
    def decorator(func):
        @wraps(func)
        def command_func(message, *args, **kwargs):
            bot.send_chat_action(chat_id=message.chat.id, action=action)
            return func(message, *args, **kwargs)
        return command_func
    return decorator


# start command handler
@bot.message_handler(commands=['start'])
@send_action('typing')
def start_command_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Hello, {0}, please choose command from the menu'.format(
        message.chat.username))
    help_command_handler(message)


# order command handler
@bot.message_handler(commands=['order'])
@send_action('typing')
def order_command_handler(message):
    chat_id = message.chat.id
    user_steps[chat_id] = 1
    bot.send_message(chat_id, '{0}, write ID of order please'.format(
        message.chat.username))


# order information command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
@send_action('typing')
def order_information_command_handler(message):
    chat_id = message.chat.id
    order_id = message.text.strip()

    try:
        order = order_service.get_order_information(order_id)
    except Exception as e:
        raise e

    user_steps[chat_id] = 0
    with codecs.open('templates/order.html', 'r', encoding='UTF-8') as file:
        template = Template(file.read())
        print(order.items)
        bot.send_message(chat_id, template.render(
            order=order), parse_mode='HTML')


# help command handler
@bot.message_handler(commands=['help'])
@send_action('typing')
def help_command_handler(message):
    chat_id = message.chat.id
    help_text = 'The following commands are available \n'
    for key in commands:
        help_text += '/' + key + ': '
        help_text += commands[key] + '\n'
    help_text += 'CRM Bot speaks english, be careful and take care'
    bot.send_message(chat_id, help_text)


# contacts command handler
@bot.message_handler(commands=['contacts'])
@send_action('typing')
def contacts_command_handler(message):
    chat_id = message.chat.id
    with codecs.open('templates/contacts.html', 'r', encoding='UTF-8') as file:
        template = Template(file.read())
        bot.send_message(chat_id, template.render(
            user_name=message.chat.username), parse_mode='HTML')


# contacts command handler
@bot.message_handler(commands=['contacts'])
@send_action('typing')
def contacts_command_handler(message):
    cid = message.chat.id
    with codecs.open('templates/contacts.html', 'r', encoding='UTF-8') as file:
        template = Template(file.read())
        bot.send_message(cid, template.render(
            user_name=message.chat.username), parse_mode='HTML')


# set web hook
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200


@app.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=SERVER_URL + '/' + TOKEN)
    return '', 200


# application entry point
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(
        os.environ.get('PORT', 8585)),  debug=True)


# if __name__ == '__main__':
#     bot.polling(none_stop=True, interval=0)
