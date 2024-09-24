import os
import random
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai  # Optional for GPT-based responses (You can skip this if not using GPT)

# Initialize OpenAI API key (if using GPT for enhanced conversation)
openai.api_key = os.getenv('OPENAI_API_KEY')  # Store API key securely in environment variables

# Load or initialize the learning data
def load_data():
    try:
        with open('responses.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open('responses.json', 'w') as file:
        json.dump(data, file)

# Initialize response data
learning_data = load_data()

# Default sample responses
default_responses = [
    "I miss you! ❤",
    "What are you up to today?",
    "You're the best! 😘",
]

# Start command with onboarding instructions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = '''Welcome to your AI Girlfriend Bot! 💖
Here’s what I can do:
1. Chat with me using /girlfriend or just type anything!
2. Ask for images using /sendimage.
3. Rate my responses by replying with 'good' or 'bad', and I’ll learn from feedback!'''
    
    # Display an interactive keyboard for fun engagement
    reply_markup = ReplyKeyboardMarkup([['I miss you! 😘', 'How’s your day?']], resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# Send a static image or multimedia
async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    image_path = 'path/to/your/image.jpg'  # Replace with actual image path
    await update.message.reply_photo(photo=open(image_path, 'rb'))

# Optionally: Send a fun GIF to make the interaction engaging
async def send_gif(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    gif_url = 'https://media.giphy.com/media/your_gif_link_here/giphy.gif'
    await update.message.reply_animation(animation=gif_url)

# Generate a conversation response
async def girlfriend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    
    # Use OpenAI GPT (optional) for more dynamic responses
    # Comment this block out if not using GPT
    response = openai.Completion.create(
        engine="gpt-4",  # Replace with any GPT model you want to use
        prompt=user_message,
        max_tokens=150
    ).choices[0].text.strip()

    # If GPT is not used, fall back to learning_data or default responses
    if not response:
        response = learning_data.get(user_message, random.choice(default_responses))
    
    await update.message.reply_text(response)
    
    # Ask for feedback on the response
    await update.message.reply_text("How was that response? (Reply with 'good', 'bad', or suggest a new response)")

    # Store the last message for feedback learning
    context.user_data['last_message'] = user_message

# Handle feedback from the user
async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_feedback = update.message.text.lower()
    last_message = context.user_data.get('last_message', None)

    # If the bot is awaiting a new response suggestion after negative feedback
    if context.user_data.get('awaiting_new_response', False):
        # Save the user's suggested new response
        learning_data[last_message] = user_feedback
        save_data(learning_data)
        await update.message.reply_text("Got it! I'll remember that for next time.")
        context.user_data['awaiting_new_response'] = False
    else:
        if user_feedback == 'good':
            await update.message.reply_text("I'm glad you liked it!")
        elif user_feedback == 'bad':
            await update.message.reply_text("I'm sorry! What should I say instead?")
            context.user_data['awaiting_new_response'] = True
        else:
            await update.message.reply_text("Thanks for the feedback!")

    # Store the last message for future interactions
    context.user_data['last_message'] = update.message.text

# Handle errors gracefully
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Oops, something went wrong! Please try again.")
    print(f"Error: {context.error}")  # Log the error for debugging

async def main() -> None:
    # Initialize the bot with your Telegram API token
    application = Application.builder().token(os.getenv('TELEGRAM_API_KEY')).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sendimage", send_image))
    application.add_handler(CommandHandler("sendgif", send_gif))
    application.add_handler(CommandHandler("girlfriend", girlfriend))
    
    # General feedback handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, feedback))
    
    # Error handling
    application.add_error_handler(error)

    # Start the bot
    await application.start_polling()
    await application.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

