import sqlite3

from telebot import types


async def choose_discipline():  # Keyboard markup maker for disciplines
    markup = types.InlineKeyboardMarkup()
    key_apex = types.InlineKeyboardButton(text="Apex", callback_data="Apex")
    key_cs = types.InlineKeyboardButton(text="CS", callback_data="CS")
    key_dota = types.InlineKeyboardButton(text="Dota 2", callback_data="Dota 2")
    key_subs = types.InlineKeyboardButton(text="Выбранные турниры", callback_data="Subs")
    markup.add(key_apex)
    markup.add(key_cs)
    markup.add(key_dota)
    markup.add(key_subs)
    return markup


async def subscriptions():  # keyboard markup maker for subs menu
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Назад", callback_data='Back disciplines'))
    return markup


async def start_menu():  # Main menu from which you can select (no return to this menu 13.09)
    markup = types.InlineKeyboardMarkup()
    key_subs = types.InlineKeyboardButton(text="Выбранные турниры", callback_data="Subs")
    key_disciplines = types.InlineKeyboardButton(text="Выбрать дисциплину", callback_data="choose discipline")
    markup.add(key_subs)
    markup.add(key_disciplines)
    return markup


async def search_for_tier():  # Keyboard markup maker for choosing tiers
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("S", callback_data="S"))
    markup.add(types.InlineKeyboardButton("A", callback_data="A"))
    markup.add(types.InlineKeyboardButton("B", callback_data="B"))
    markup.add(types.InlineKeyboardButton("Назад к выбору дисциплины", callback_data="Back"))
    return markup


async def for_tournaments(tournaments, tier, user_id):  # Keyboard markup for 10 tournaments of specific tier user choosed
    markup = types.InlineKeyboardMarkup()
    tournaments_prize = []
    connection = sqlite3.connect("../DataBases/NotificationBotDB.db")
    cursor = connection.cursor()
    user_tournaments = cursor.execute('SELECT TournamentsSelected FROM UserInfo WHERE UserID = ?', (user_id,))
    try:
        user_tournaments = user_tournaments.fetchone()[0].split(',')
    except Exception:
        print('a')
    for i in tournaments:
        if i["tier"] == tier:
            tournaments_prize.append((i['tournament'], i['prize']))
    tournaments_prize = sorted(tournaments_prize, key=lambda x: x[1] if x[1] == 0 else float(''.join(x[1][1:].split(','))) if x[1] != '\xa0' else 0)
    for t in tournaments_prize[:10]:
        if t[0] in user_tournaments:
            markup.add(types.InlineKeyboardButton(t[0] + '✅', callback_data="{" + "+" + t[0]))
        else:
            markup.add(types.InlineKeyboardButton(t[0] + '❌', callback_data="{" + "+" + t[0]))
    if len(markup.keyboard) == 0:
        markup.add(types.InlineKeyboardButton("Сейчас турниров такого тира не ожидается", callback_data="Back"))
    markup.add(types.InlineKeyboardButton("Назад к выбору тира", callback_data="Back tier"))
    connection.close()
    return markup


async def delete_notification(tournament):  # Menu for deleting or not tournament from subs
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Да", callback_data="Delete" + "+" + tournament))
    markup.add(types.InlineKeyboardButton("Нет", callback_data="Mistake"))
    return markup