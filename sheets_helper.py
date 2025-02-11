import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class SheetsHelper:
    def __init__(self):
        """Initialize the Google Sheets helper."""
        from dotenv import load_dotenv
        load_dotenv()  # Load environment variables
        
        self.SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
        if not self.SPREADSHEET_ID:
            raise ValueError("SPREADSHEET_ID not found in environment variables")
            
        self.SHEET_NAME = 'Sheet1'  # Changed to Sheet1 since it's the default sheet
        
        try:
            # Load credentials
            logger.debug("Loading service account credentials...")
            creds = service_account.Credentials.from_service_account_file(
                'service_account.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            logger.info("Successfully loaded credentials")
            
            # Create service
            logger.debug("Initializing Google Sheets service...")
            self.service = build('sheets', 'v4', credentials=creds)
            self.sheet = self.service.spreadsheets()
            logger.info("Successfully initialized Google Sheets service")
            
        except Exception as e:
            logger.error(f"Failed to initialize sheets helper: {str(e)}")
            raise
            
    def setup_sheet(self, force_recreate=False):
        """Set up the responses sheet with headers."""
        try:
            # Load questions
            with open('questions.json', 'r') as f:
                questions = json.load(f)['quiz']
                
            # Create headers
            headers = ['User']  # Add user column first
            for q in questions:
                headers.append(q['question'])
            headers.append('Timestamp')  # Add timestamp column
            
            # Get sheet metadata
            sheet_metadata = self.sheet.get(spreadsheetId=self.SPREADSHEET_ID).execute()
            sheets = sheet_metadata.get('sheets', '')
            
            # Check if sheet exists
            sheet_exists = False
            for s in sheets:
                if s['properties']['title'] == self.SHEET_NAME:
                    sheet_exists = True
                    sheet_id = s['properties']['sheetId']
                    break
                    
            if not sheet_exists:
                # Create new sheet
                body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': self.SHEET_NAME
                            }
                        }
                    }]
                }
                self.sheet.batchUpdate(
                    spreadsheetId=self.SPREADSHEET_ID,
                    body=body
                ).execute()
                logger.info(f"Created new sheet: {self.SHEET_NAME}")
                
            # Get current headers
            range_name = f'{self.SHEET_NAME}!A1:Z1'
            result = self.sheet.values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=range_name
            ).execute()
            current_headers = result.get('values', [[]])[0] if result.get('values') else []
            
            logger.info(f"Found {len(current_headers)} headers")
            
            # Check if headers match
            if force_recreate or current_headers != headers:
                # Clear sheet
                self.sheet.values().clear(
                    spreadsheetId=self.SPREADSHEET_ID,
                    range=f'{self.SHEET_NAME}!A:Z'
                ).execute()
                
                # Update headers
                body = {
                    'values': [headers]
                }
                self.sheet.values().update(
                    spreadsheetId=self.SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                # Format headers
                body = {
                    'requests': [{
                        'repeatCell': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {
                                        'red': 0.8,
                                        'green': 0.8,
                                        'blue': 0.8
                                    },
                                    'textFormat': {
                                        'bold': True
                                    }
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    }]
                }
                self.sheet.batchUpdate(
                    spreadsheetId=self.SPREADSHEET_ID,
                    body=body
                ).execute()
                
                logger.info("Updated headers and formatting")
                
            return True
            
        except Exception as e:
            logger.error(f"Error setting up sheet: {str(e)}")
            return False
            
    def test_setup(self):
        """Test if the sheet is set up correctly."""
        try:
            # Load questions
            with open('questions.json', 'r') as f:
                questions = json.load(f)['quiz']
                
            # Get current headers
            range_name = f'{self.SHEET_NAME}!A1:Z1'
            result = self.sheet.values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=range_name
            ).execute()
            
            if not result.get('values'):
                logger.error("✗ No headers found")
                return False
                
            current_headers = result['values'][0]
            logger.info(f"✓ Found {len(current_headers)} headers")
            
            # Check header count
            expected_count = len(questions) + 2  # +1 for timestamp, +1 for user
            if len(current_headers) != expected_count:
                logger.error(f"✗ Header count mismatch. Expected {expected_count}, got {len(current_headers)}")
                return False
                
            logger.info("✓ Header count matches questions")
            return True
            
        except Exception as e:
            logger.error(f"Error testing setup: {str(e)}")
            return False
            
    def append_row(self, row_data):
        """Append a row of data to the sheet."""
        try:
            logger.info(f"Appending row to sheet {self.SHEET_NAME}")
            result = self.sheet.values().append(
                spreadsheetId=self.SPREADSHEET_ID,
                range=f"{self.SHEET_NAME}!A2",  # Start from A2 to preserve headers
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row_data]}
            ).execute()
            logger.info(f"Append result: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to append row: {str(e)}")
            return False
