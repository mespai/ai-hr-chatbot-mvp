import gspread
from google.oauth2.service_account import Credentials

# --- Setup Google Sheets Access ---
def connect_to_sheets(sheet_name):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_file(
        "credentials.json", scopes=scopes
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open(sheet_name)
    return spreadsheet.sheet1  # Open first sheet

def log_interaction(sheet, user_email, user_input, bot_response, feedback):
    sheet.append_row([user_email, user_input, bot_response, feedback])
    