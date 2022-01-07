import telebot
import os
import codecs

from functools import wraps
from telebot import types
from jinja2 import Template
from dotenv import load_dotenv
from flask import Flask, request
from services.order_service import OrderService
from services.customer_service import CustomerService
from services.reports_service import ReportsService


load_dotenv()

# bot initialization
TOKEN = os.getenv('API_BOT_TOKEN')
SERVER_URL = os.getenv('SERVER_URL')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

order_steps = {}
order_service = OrderService()

history_steps = {}
customer_service = CustomerService()

reports_service = ReportsService()

commands = {
    'start': 'Start using this bot',
    'order': 'Please, write an Order Id',
    'history': 'Please, write an Customer Id',
    'help': 'Useful information about this bot',
    'contacts': 'Developer contacts',
}


def get_user_step(uid, obj):
    if uid not in obj:
        obj[uid] = 0
    return obj[uid]


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
    order_steps[chat_id] = 1
    bot.send_message(chat_id, 'Write ID of order please')


# order information command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id, order_steps) == 1)
@send_action('typing')
def order_information_command_handler(message):
    chat_id = message.chat.id
    order_id = message.text.strip()

    try:
        json = order_service.get_order_information(order_id)
    except ValueError as e:
        order_steps[chat_id] = 0
        return bot.send_message(chat_id, f'❌ {e}')

    order_steps[chat_id] = 0
    items = [v for v in json['items'].values()]
    fulfillments = [f for f in json['fulfillments']]

    with codecs.open('templates/order.html', 'r', encoding='UTF-8') as file:
        template = Template(file.read())

        bot.send_message(chat_id, template.render(
            order=json, items=items, fulfillments=fulfillments), parse_mode='HTML')


# history command handler
@bot.message_handler(commands=['history'])
@send_action('typing')
def history_command_handler(message):
    chat_id = message.chat.id
    history_steps[chat_id] = 1
    bot.send_message(chat_id, 'Write ID of customer please')


# history information command handler
@bot.message_handler(func=lambda message: get_user_step(message.chat.id, history_steps) == 1)
@send_action('typing')
def history_information_command_handler(message):
    chat_id = message.chat.id
    customer_id = message.text.strip()

    try:
        history = customer_service.get_customer_history(customer_id)
    except ValueError as e:
        order_steps[chat_id] = 0
        return bot.send_message(chat_id, f'❌ {e}')

    history_steps[chat_id] = 0

    with codecs.open('templates/history.html', 'r', encoding='UTF-8') as file:
        template = Template(file.read())

        bot.send_message(chat_id, template.render(
            customer_id=customer_id, history=history), parse_mode='HTML')


# summaryreport command handler
@bot.message_handler(commands=['summaryreport'])
@send_action('typing')
def summaryreport_command_handler(message):
    chat_id = message.chat.id

    try:
        mids = reports_service.get_mid_summary_report()
    except ValueError as e:
        order_steps[chat_id] = 0
        return bot.send_message(chat_id, f'❌ {e}')

    with codecs.open('templates/summary_report.html', 'r', encoding='UTF-8') as file:
        template = Template(file.read())

        bot.send_message(chat_id, template.render(
            mids=mids), parse_mode='HTML')


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
            username=message.chat.username), parse_mode='HTML')


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
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=int(
#         os.environ.get('PORT', 8585)),  debug=True)


if __name__ == '__main__':
    bot.remove_webhook()
    bot.polling(none_stop=True, interval=0)
