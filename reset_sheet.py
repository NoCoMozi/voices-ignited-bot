from sheets_helper import SheetsHelper

def main():
    sheets = SheetsHelper()
    print("Forcing sheet recreation...")
    result = sheets.setup_sheet(force_recreate=True)
    print(f"Sheet recreation {'successful' if result else 'failed'}")
    
if __name__ == "__main__":
    main()
