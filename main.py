import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import openpyxl
import os

API_TOKEN = '6923809067:AAGAK63pcW2iwzupME2TMBJ_4Uogsk0Fsf8'

bot = telebot.TeleBot(API_TOKEN, threaded=False)

cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}

bot.user_data = {}  # Инициализируем user_data

def calculate_score(hand):
    score = sum(values[card] for card in hand)
    aces = hand.count('A')
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

def record_game_result(user_id, player_hand, dealer_hand, result):
    file_name = 'game_results.xlsx'
    
    if os.path.exists(file_name):
        wb = openpyxl.load_workbook(file_name)
    else:
        wb = openpyxl.Workbook()
        wb.active.append(['User ID', 'Player Hand', 'Dealer Hand', 'Result'])
    
    ws = wb.active
    ws.append([user_id, ', '.join(player_hand), ', '.join(dealer_hand), result])
    wb.save(file_name)

@bot.message_handler(commands=['rules'])
def send_rules(message):
    rules_text = (
        "Правила игры в 21 (Blackjack):\n"
        "1. Цель игры - набрать сумму очков близкую к 21, не превышая ее.\n"
        "2. Каждая карта имеет свое значение: от 2 до 10 - по номиналу, карты J, Q, K - по 10, A - 1 или 11.\n"
        "3. Игрок и дилер получают по две карты. Одна из карт дилера остается скрытой.\n"
        "4. Игрок может брать дополнительные карты (hit) или останавливаться (stand).\n"
        "5. Если сумма очков у игрока превышает 21, он проигрывает (перебор).\n"
        "6. Дилер берет дополнительные карты, если сумма его очков меньше 17.\n"
        "7. Побеждает игрок, у которого сумма очков ближе к 21 без перебора или дилер, если у игрока перебор или сумма очков дилера ближе к 21."
    )

    # Создание клавиатуры с кнопкой "Ознакомлен"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Ознакомлен", callback_data='acknowledge'))

    # Отправка сообщения с правилами и клавиатурой
    msg = bot.send_message(message.chat.id, rules_text, reply_markup=markup)

@bot.message_handler(commands=['clear'])
def clear_chat(message):
    # Получаем идентификатор чата
    chat_id = message.chat.id

    # Получаем идентификатор последнего сообщения в чате
    last_message_id = message.message_id

    # Разделяем список идентификаторов сообщений на более мелкие части
    chunk_size = 100  # Размер части (может быть любым подходящим значением)
    chunks = [list(range(i, min(i + chunk_size, last_message_id))) for i in range(1, last_message_id, chunk_size)]

    # Удаляем сообщения для каждой части
    for chunk in chunks:
        bot.delete_messages(chat_id, chunk)
    bot.send_message(chat_id, "Чат был очищен. Удачи в новых начинаниях. Команда /start")




@bot.callback_query_handler(func=lambda call: call.data == 'acknowledge')
def acknowledge_rules(call):
    # Удаление сообщения с правилами после нажатия кнопки "Ознакомлен"
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    bot.user_data[user_id] = {
        'player_hand': [random.choice(cards)],
        'dealer_hand': [random.choice(cards)]
    }
    
    player_score = calculate_score(bot.user_data[user_id]['player_hand'])
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Взять карту", callback_data='hit'))
    markup.add(InlineKeyboardButton("Остановиться", callback_data='stand'))
    
    bot.send_message(
        message.chat.id,
        f"Ваши карты: {bot.user_data[user_id]['player_hand']} (сумма: {player_score})\n"
        f"Карта дилера: {bot.user_data[user_id]['dealer_hand'][0]} *\n"
        "Хотите взять еще карту?",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id

    if user_id not in bot.user_data:
        bot.send_message(call.message.chat.id, "Пожалуйста, начните игру сначала, используя команду /start.")
        bot.send_message(call.message.chat.id, "Правила игры /rules.")
        return

    if call.data == 'hit':
        bot.user_data[user_id]['player_hand'].append(random.choice(cards))
        player_score = calculate_score(bot.user_data[user_id]['player_hand'])
        
        if player_score > 21:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Начать заново", callback_data='restart'))
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Ваши карты: {bot.user_data[user_id]['player_hand']} (сумма: {player_score})\n"
                     "Вы перебрали! Вы проиграли.",
                reply_markup=markup
            )
            record_game_result(user_id, bot.user_data[user_id]['player_hand'], bot.user_data[user_id]['dealer_hand'], 'Проигрыш')
            bot.user_data.pop(user_id)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Взять карту", callback_data='hit'))
            markup.add(InlineKeyboardButton("Остановиться", callback_data='stand'))
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Ваши карты: {bot.user_data[user_id]['player_hand']} (сумма: {player_score})\n"
                     f"Карта дилера: {bot.user_data[user_id]['dealer_hand'][0]} *\n"
                     "Хотите взять еще карту?",
                reply_markup=markup
            )
    elif call.data == 'stand':
        dealer_score = calculate_score(bot.user_data[user_id]['dealer_hand'])
        player_score = calculate_score(bot.user_data[user_id]['player_hand'])
        
        while dealer_score < 17:
            bot.user_data[user_id]['dealer_hand'].append(random.choice(cards))
            dealer_score = calculate_score(bot.user_data[user_id]['dealer_hand'])
        
        result = ""
        if dealer_score > 21 or dealer_score < player_score:
            result = "Вы выиграли!"
        elif dealer_score > player_score:
            result = "Вы проиграли."
        else:
            result = "Ничья."
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Начать заново", callback_data='restart'))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Ваши карты: {bot.user_data[user_id]['player_hand']} (сумма: {player_score})\n"
                 f"Карты дилера: {bot.user_data[user_id]['dealer_hand']} (сумма: {dealer_score})\n"
                 f"{result}",
            reply_markup=markup
        )
        record_game_result(user_id, bot.user_data[user_id]['player_hand'], bot.user_data[user_id]['dealer_hand'], result)
        bot.user_data.pop(user_id)
    elif call.data == 'restart':
        start(call.message)

bot.polling(none_stop=True, timeout=60)
