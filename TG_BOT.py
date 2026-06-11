import requests
import telebot
import os

from flask.cli import load_dotenv
from telebot import types

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Проверь файл .env")

bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}
user_states = {}


def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("Добавить пароль")
    btn2 = types.KeyboardButton("Список паролей")
    btn3 = types.KeyboardButton("Отмена")

    markup.add(btn1, btn2)
    markup.add(btn3)

    return markup


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот-помощник Smart Password Manager.\n"
        "Через меня можно добавить пароль, а потом он появится на сайте.",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda message: message.text == "Отмена")
def cancel(message):
    chat_id = message.chat.id

    user_data.pop(chat_id, None)
    user_states.pop(chat_id, None)

    bot.send_message(chat_id, "Действие отменено.", reply_markup=main_menu())


@bot.message_handler(func=lambda message: message.text == "Добавить пароль")
def add_password_start(message):
    chat_id = message.chat.id

    user_data[chat_id] = {}
    user_states[chat_id] = "waiting_title"

    bot.send_message(chat_id, "Введите название сервиса. Например: Gmail")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_title")
def get_title(message):
    chat_id = message.chat.id
    title = message.text.strip()

    if not title:
        bot.send_message(chat_id, "Название не может быть пустым. Введите название сервиса:")
        return

    user_data[chat_id]["title"] = title
    user_states[chat_id] = "waiting_username"

    bot.send_message(chat_id, "Введите логин или email:")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_username")
def get_username(message):
    chat_id = message.chat.id
    username = message.text.strip()

    if not username:
        bot.send_message(chat_id, "Логин не может быть пустым. Введите логин:")
        return

    user_data[chat_id]["username"] = username
    user_states[chat_id] = "waiting_password"

    bot.send_message(chat_id, "Введите пароль:")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_password")
def get_password(message):
    chat_id = message.chat.id
    password = message.text.strip()

    if not password:
        bot.send_message(chat_id, "Пароль не может быть пустым. Введите пароль:")
        return

    user_data[chat_id]["password"] = password
    user_states[chat_id] = "waiting_note"

    bot.send_message(chat_id, "Введите заметку или напишите '-' если заметка не нужна:")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_note")
def get_note_and_save(message):
    chat_id = message.chat.id
    note = message.text.strip()

    if note == "-":
        note = ""

    user_data[chat_id]["note"] = note

    entry = user_data[chat_id]

    try:
        response = requests.post(
            f"{API_URL}/add",
            json={
                "title": entry["title"],
                "username": entry["username"],
                "password": entry["password"],
                "note": entry["note"]
            },
            timeout=5
        )

        if response.status_code == 201 or response.status_code == 200:
            bot.send_message(
                chat_id,
                "Запись успешно добавлена.\n"
                "Теперь она должна отображаться на сайте.",
                reply_markup=main_menu()
            )
        else:
            try:
                error_data = response.json()
                error_text = error_data.get("error", "Неизвестная ошибка")
            except Exception:
                error_text = response.text

            bot.send_message(
                chat_id,
                f"Ошибка при добавлении записи:\n{error_text}",
                reply_markup=main_menu()
            )

    except requests.exceptions.ConnectionError:
        bot.send_message(
            chat_id,
            "Не удалось подключиться к Flask API.\n"
            "Проверь, что запущен api_server.py",
            reply_markup=main_menu()
        )

    except requests.exceptions.Timeout:
        bot.send_message(
            chat_id,
            "Flask API слишком долго не отвечает.",
            reply_markup=main_menu()
        )

    finally:
        user_data.pop(chat_id, None)
        user_states.pop(chat_id, None)


@bot.message_handler(func=lambda message: message.text == "Список паролей")
def list_password(message):
    chat_id = message.chat.id
    try:
        response = requests.get(f"{API_URL}/entries", timeout=5)

        if response.status_code != 200:
            bot.send_message(chat_id, "Ошибка при получении списка паролей.")
            return

        entries = response.json()

        if not entries:
            bot.send_message(chat_id, "Список паролей пуст.")
            return

        text_lines = ["Список записей:\n"]

        for index, entry in enumerate(entries, start=1):
            text_lines.append(
                f"{index}. {entry.get('title', 'Без названия')}\n"
                f"Логин: {entry.get('username', '')}\n"
                f"Пароль: {entry.get('password', '')}\n"
                f"Заметка: {entry.get('note', '')}\n"
            )

        bot.send_message(chat_id, "\n".join(text_lines))

    except requests.exceptions.ConnectionError:
        bot.send_message(
            chat_id,
            "Не удалось подключиться к Flask API.\n"
            "Проверь, что запущен api_server.py"
        )


@bot.message_handler(content_types=["text"])
def unknown_message(message):
    bot.send_message(
        message.chat.id,
        "Я не понял команду. Используйте кнопки меню.",
        reply_markup=main_menu()
    )


print("Telegram-бот запущен...")
bot.polling(non_stop=True, interval=0)

