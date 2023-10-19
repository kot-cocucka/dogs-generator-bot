import json
import logging
import random
import sqlite3
import os

import argparse

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


DB_PATH = None

TOKEN = os.environ['TOKEN']
break_generator_chance = 5

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"An error occurred: {context.error}")
    update.message.reply_text("В этот раз что-то сломалось по-настоящему. Попробуйте еще раз.")

def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Добро пожаловать в Генератор Собак!\n"
        "Как пользоваться генератором:\n"
        "/generate - Сгенерировать собак.\n"
        "/stats - Посмотреть статистику генерации."
    )
    update.message.reply_text(welcome_message, parse_mode='Markdown')

def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Как пользоваться генератором:\n"
        "/generate - Сгенерировать собак.\n"
        "/stats - Посмотреть статистику генерации."
    )
    update.message.reply_text(help_text)

def get_user_identity(update: Update) -> str:
    try:
        user_identity = (
            update.message.from_user.username
            or update.message.from_user.first_name
        )
        return user_identity
    except Exception as e:
        logger.exception(e)
        return str(update.message.from_user.id)


def generate_dogs(num):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name, url FROM breeds ORDER BY RANDOM() LIMIT ?", (num,))
    random_breeds = cursor.fetchall()
    conn.close()

    counts = []
    for _ in range(len(random_breeds) - 1):
        try:
            count = random.randint(1, num - sum(counts))
            counts.append(count)
        except ValueError:
            break

    return list(zip([f"[{breed[0]}]({breed[1]})" for breed in random_breeds], counts))

def generate_dog_stats(num_dogs):
    breeds_with_counts = generate_dogs(num_dogs)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for breed, count in breeds_with_counts:
        breed_name = breed.split("](")[0][1:] 
        cursor.execute("UPDATE breeds SET total_generated = total_generated + ? WHERE name = ?", (count, breed_name))
    conn.commit()

    cursor.execute("SELECT name, total_generated, url FROM breeds ORDER BY total_generated DESC LIMIT 5")
    top_breeds = cursor.fetchall()

    if len(top_breeds) < 5:
        top_breeds = cursor.execute("SELECT name, total_generated, url FROM breeds ORDER BY total_generated DESC").fetchall()

    conn.close()

    return f"Сгенерировано собак - {num_dogs}.\n\nИз них:\n" + "\n".join([f"🐶 {breed[0]} - {breed[1]}" for breed in breeds_with_counts])


with open("src/causes.json", "r", encoding="utf-8") as file:
    causes_data = json.load(file)
    causes = causes_data["causes"]
    implies = causes_data["implies"]

def gen(update: Update, context: CallbackContext) -> None:
    user_identity = get_user_identity(update)
    logger.info(f"{user_identity} wants some dogs")

    if random.randint(1, 100) <= break_generator_chance:
        cause_of_break = random.choice(causes)
        reply_text = f"⛔️ {cause_of_break}.\n {random.choice(implies)}"
        update.message.reply_text(reply_text, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        num_dogs = random.randint(10, 100)
        result = generate_dog_stats(num_dogs)
        update.message.reply_text(result, parse_mode='Markdown', disable_web_page_preview=True)

def stats(update: Update, context: CallbackContext) -> None:
    user_identity = get_user_identity(update)
    logger.info(f"{user_identity} wants to know stats")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(total_generated) FROM breeds")
    total_generated = cursor.fetchone()[0]

    cursor.execute("SELECT name, total_generated, url FROM breeds ORDER BY total_generated DESC LIMIT 10")
    top_breeds = cursor.fetchall()

    if len(top_breeds) < 10:
        top_breeds = cursor.execute("SELECT name, total_generated, url FROM breeds ORDER BY total_generated DESC").fetchall()

    markdown_breeds = [f"🐶 [{breed[0]}]({breed[2]}) - {breed[1]}" for breed in top_breeds]
    message_text = f"Всего собак было сгенерировано: {total_generated}\n\nСтатистика генерации:\n" + "\n".join(markdown_breeds)

    update.message.reply_text(message_text, parse_mode="Markdown", disable_web_page_preview=True)
    conn.close()

def parse_args():
    parser = argparse.ArgumentParser(description="A Telegram bot that generates random dog breeds.")
    parser.add_argument("--db-path", help="The path to the SQLite database file.")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    DB_PATH = args.db_path

    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("gen", gen))
    dispatcher.add_handler(CommandHandler("generate", gen))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

