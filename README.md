# Voices Ignited Quiz Bot 

A Telegram bot that helps collect responses from potential movement members through an interactive quiz. The responses are automatically saved to a Google Sheet for easy analysis.

## Features

- Interactive quiz with multiple question types (multiple choice, yes/no, text)
- Automatic response collection in Google Sheets
- Clean interface with message cleanup
- User tracking with Telegram usernames
- Timestamp recording for each response

## Setup

1. Clone this repository:
```bash
git clone [your-repo-url]
cd voices-ignited-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
BOT_TOKEN=your_telegram_bot_token
SPREADSHEET_ID=your_google_sheets_id
```

4. Set up Google Sheets:
- Create a Google Cloud project
- Enable Google Sheets API
- Create a service account
- Download the service account key as `service_account.json`
- Share your Google Sheet with the service account email

## Running the Bot

```bash
python main.py
```

## Project Structure

- `main.py`: Main bot logic and handlers
- `sheets_helper.py`: Google Sheets integration
- `questions.json`: Quiz questions configuration
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (not in repo)
- `service_account.json`: Google service account key (not in repo)

## Contributing

Feel free to submit issues and pull requests to improve the bot.

## License

This project is licensed under the MIT License - see the LICENSE file for details.