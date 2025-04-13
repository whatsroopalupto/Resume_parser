from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path
import json

# Update the RANGE_NAME constant
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]
SPREADSHEET_ID = 'ENTER YOUR GOOGLE SPREADSHEET ID' # change it with your google spreadsheet id for more detail go through the readme page
RANGE_NAME = 'Sheet1'  # Change to match your actual sheet name
CREDS_FILE = r'PATH TO YOUR CREDENTIALS FILE' # Create the credentials file from google cloud console and paste the path here

class SheetsManager:
    def __init__(self):
        self.creds = None
        self.service = None
        try:
            self.authenticate()
            # Use the correct RANGE_NAME constant
            self.setup_sheet()
            self.test_connection()
        except Exception as e:
            print(f"Initialization error: {str(e)}")
            raise

    def setup_sheet(self):
        """Setup sheet headers if they don't exist"""
        try:
            headers = [
                'Name', 'Email', 'Phone', 'Skills', 'Resume Score', 
                'ATS Recommendation', 'Degree', 'Institution', 
                'Work Experience', 'Number of Projects', 
                'Number of Certifications', 'CGPA'
            ]
            
            # Fix the range reference
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!A1:L1'  # Use direct sheet name
            ).execute()
            
            if 'values' not in result:
                self.service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range='Sheet1!A1',  # Use direct sheet name
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
        except Exception as e:
            print(f"Error setting up sheet: {str(e)}")

    # Update the range reference in add_candidate method
    def add_candidate(self, parsed_data):
        try:
            # Clean email (remove emojis and unwanted characters)
            email = parsed_data.get('email', '')
            email = ''.join(char for char in email if ord(char) < 128 and char != '✉').strip()
            if '@' not in email:
                # Try to find email in the parsed data
                for key, value in parsed_data.items():
                    if isinstance(value, str) and '@' in value and '.com' in value.lower():
                        email = value.strip()
                        break

            # Get education info before using it
            education_info = parsed_data.get('education', [{}])[0]
            degree = education_info.get('degree', '')
            institution = education_info.get('institution', '')
            
            # Format phone number
            phone = parsed_data.get('phone', '').replace('-', '')
            
            values = [[
                parsed_data.get('name', ''),
                email,  # Use cleaned email
                phone,
                ', '.join(parsed_data.get('skills', [])),
                parsed_data.get('resume_score', '0/100'),
                parsed_data.get('ats_recommendation', ''),
                degree,
                institution,
                ', '.join([f"{exp.get('company', '')} - {exp.get('role', '')}" 
                          for exp in parsed_data.get('work_experience', [])]),
                len(parsed_data.get('projects', [])),
                len(parsed_data.get('certifications', [])),
                education_info.get('cgpa', 'N/A')
            ]]

            # Fix the range reference and ensure data is added
            result = self.service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!A:L',  # Use full column range
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': values}
            ).execute()
            print(f"Data added successfully: {result}")
            return True

        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return False

    # Update the range reference in test_connection method
    def test_connection(self):
        """Test the connection to Google Sheets"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!A1'  # Use direct sheet name
            ).execute()
            print("✅ Successfully connected to Google Sheets!")
            print(f"Sheet access test result: {result}")
        except HttpError as e:
            print(f"❌ Sheet access error: {str(e)}")
            if "403" in str(e):
                print("Please make sure the sheet is shared with your Google account")
            raise

    def authenticate(self):
        print(f"🔍 Looking for credentials file at: {CREDS_FILE}")
        if not os.path.exists(CREDS_FILE):
            raise FileNotFoundError(f"❌ Credentials file not found at: {CREDS_FILE}")
        
        print("🔑 Starting authentication process...")
        if os.path.exists('token.json'):
            try:
                self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                print("📄 Found existing token.json")
            except Exception as e:
                print(f"❌ Error with token.json: {str(e)}")
                os.remove('token.json')
                self.creds = None
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"❌ Error refreshing credentials: {str(e)}")
                    os.remove('token.json')
                    self.creds = None
            
            if not self.creds:
                print("🔄 Getting new credentials...")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
                    # Use local server with a specific port
                    self.creds = flow.run_local_server(port=8080, 
                                                     prompt='consent',
                                                     access_type='offline')
                    
                    with open('token.json', 'w') as token:
                        token.write(self.creds.to_json())
                    print("✅ New token.json created")
                except Exception as e:
                    print(f"❌ Authentication flow error: {str(e)}")
                    raise

        self.service = build('sheets', 'v4', credentials=self.creds)
        print("✅ Authentication completed")
