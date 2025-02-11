from sheets_helper import SheetsHelper
import logging

logging.basicConfig(level=logging.DEBUG)

def test_sheets():
    try:
        print("Initializing sheets helper...")
        helper = SheetsHelper()
        
        print("Setting up sheet...")
        helper.setup_sheet()
        
        print("Testing row append...")
        test_row = ["25", "US State", "Test response", "2025-02-10"]
        success = helper.append_row(test_row)
        
        if success:
            print("Successfully added test row!")
        else:
            print("Failed to add test row")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_sheets()
