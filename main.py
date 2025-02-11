import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

from sheets_helper import SheetsHelper

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
print(f"DEBUG: Bot token loaded: {'YES' if BOT_TOKEN else 'NO'}")
print(f"DEBUG: Token starts with: {BOT_TOKEN[:10] + '...' if BOT_TOKEN else 'None'}")

class QuizBot:
    def __init__(self):
        try:
            if not BOT_TOKEN:
                raise ValueError("BOT_TOKEN not found in environment variables")
                
            self.updater = Updater(BOT_TOKEN)
            self.dispatcher = self.updater.dispatcher
            self.sheets = SheetsHelper()
            
            # Load questions
            with open('questions.json', 'r') as f:
                self.questions = json.load(f)['quiz']
                
            # Validate questions
            for q in self.questions:
                if 'type' not in q or 'question' not in q:
                    raise ValueError(f"Invalid question format: {q}")
                if q['type'] not in ['yes_no', 'multiple_choice', 'number']:
                    logger.warning(f"Question type {q['type']} may not be fully supported")
            
            # Add handlers
            self.dispatcher.add_handler(CommandHandler('start', self.start))
            self.dispatcher.add_handler(CommandHandler('quiz', self.quiz))
            self.dispatcher.add_handler(CallbackQueryHandler(self.handle_button))
            self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))
            
            logger.info("Bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {str(e)}")
            raise
        
    def start(self, update: Update, context: CallbackContext):
        print("DEBUG: /start command received")
        try:
            welcome_message = (
                "Hello and welcome to Voices Ignited! 🔥\n\n"
                "We are a movement fighting for a government that truly serves its people, not corporations.\n"
                "This short quiz will help us understand your values and how you'd like to contribute.\n"
                "Let's stand together for justice, equality, and real change—let's get started! 🚀\n\n"
                "Use /quiz to begin!"
            )
            print("DEBUG: Sending welcome message")
            print(f"DEBUG: Chat ID = {update.message.chat_id}")
            result = update.message.reply_text(welcome_message)
            print("DEBUG: Welcome message sent successfully")
        except Exception as e:
            print(f"DEBUG: Error in start command: {str(e)}")
            logger.error(f"Error in start command: {str(e)}")
        
    def quiz(self, update: Update, context: CallbackContext):
        # Clear any previous quiz data
        context.user_data['current_question'] = 0
        context.user_data['answers'] = {}
        context.user_data['message_ids'] = []
        
        # Store user info at the start
        user = update.message.from_user
        context.user_data['user_id'] = user.id
        context.user_data['username'] = user.username
        
        # Store the /quiz command message for cleanup
        context.user_data['message_ids'].append(update.message.message_id)
        
        # Send first question
        self.send_question(update.message, context)
        
    def send_question(self, message, context: CallbackContext):
        q_index = context.user_data.get('current_question', 0)
        
        if q_index >= len(self.questions):
            self.finish_quiz(message, context)
            return
            
        question = self.questions[q_index]
        text = f"Question {q_index + 1}: {question['question']}"
        
        # Store the question message ID for later deletion
        sent_msg = None
        if question.get('type') == 'yes_no':
            keyboard = [
                [InlineKeyboardButton("Yes", callback_data="Yes")],
                [InlineKeyboardButton("No", callback_data="No")]
            ]
            sent_msg = message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif 'options' in question:
            # For multiple choice, use numbers as callback data
            keyboard = []
            for i, opt in enumerate(question['options']):
                keyboard.append([InlineKeyboardButton(f"{i+1}. {opt}", callback_data=str(i))])
            sent_msg = message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            sent_msg = message.reply_text(text)
            
        # Store the message ID for later cleanup
        if sent_msg:
            context.user_data['message_ids'].append(sent_msg.message_id)
            
    def handle_button(self, update: Update, context: CallbackContext):
        query = update.callback_query
        q_index = context.user_data.get('current_question', 0)
        question = self.questions[q_index]
        
        # Get answer text
        if question.get('type') == 'yes_no':
            answer = query.data
        else:
            # For multiple choice, get the full option text
            answer = question['options'][int(query.data)]
            
        # Save answer
        context.user_data['answers'][str(q_index)] = answer
        context.user_data['current_question'] = q_index + 1
        
        # Delete old message and show new one
        try:
            query.message.delete()
        except:
            pass  # Ignore if we can't delete the message
            
        # Next question
        self.send_question(query.message, context)
        
    def handle_text(self, update: Update, context: CallbackContext):
        q_index = context.user_data.get('current_question', 0)
        
        if q_index >= len(self.questions):
            update.message.reply_text("Quiz is finished. Use /quiz to start again.")
            return
            
        # Store user's message ID for cleanup
        context.user_data['message_ids'].append(update.message.message_id)
        
        # Save answer
        context.user_data['answers'][str(q_index)] = update.message.text
        context.user_data['current_question'] = q_index + 1
        
        # Next question
        self.send_question(update.message, context)
            
    def finish_quiz(self, message, context: CallbackContext):
        # Clean up all stored messages
        message_ids = context.user_data.get('message_ids', [])
        for msg_id in message_ids:
            try:
                context.bot.delete_message(chat_id=message.chat_id, message_id=msg_id)
            except:
                pass
                
        answers = context.user_data.get('answers', {})
        row = []
        
        # Add user information from stored data
        username = context.user_data.get('username')
        user_id = context.user_data.get('user_id')
        identifier = f"@{username}" if username else f"id:{user_id}"
        row.append(identifier)
        
        # Format answers in order
        for i in range(len(self.questions)):
            answer = answers.get(str(i), '')
            row.append(str(answer))
            
        # Add timestamp
        row.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Save to sheets
        if self.sheets.append_row(row):
            # Send thank you message
            message.reply_text(
                "Thank you for completing the quiz! 🙏\n\n"
                "Your responses have been recorded. Together, we can make a difference! ✊",
                reply_markup=None  # Remove any inline keyboard
            )
        else:
            message.reply_text("Error saving responses. Please try again.")
            
        # Clear stored message IDs
        context.user_data['message_ids'] = []
            
    def run(self):
        try:
            logger.info("Starting bot...")
            print("DEBUG: Bot starting up...")
            self.updater.start_polling()
            print("DEBUG: Bot polling started")
            logger.info("Bot started successfully")
            self.updater.idle()
        except Exception as e:
            logger.error(f"Error running bot: {str(e)}")
            print(f"DEBUG: Error running bot: {str(e)}")
            raise

if __name__ == '__main__':
    bot = QuizBot()
    bot.run()
