# Resume_parser
A Python application that parses resumes (PDF), extracts information using Groq AI, calculates an ATS score, and stores the data in Google Sheets.



## Features

- PDF resume parsing
- AI-powered information extraction using Groq AI
- ATS scoring system
- Google Sheets integration
- Desktop GUI application
- Web interface

## Prerequisites

- Python 3.8+
- Google Cloud Platform account
- Groq AI API key
- Google Sheets API enabled

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ResumeParser
```

2. Install required packages:
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client PyPDF2 requests flask
```

## Setup

### 1. Groq AI Setup
1. Sign up at [Groq Cloud](https://console.groq.com)
2. Generate an API key
3. Replace `GROQ_API_KEY` in `resume_parser.py`:
```python
GROQ_API_KEY = "your-groq-api-key"
```

### 2. Google Sheets Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Google Sheets API:
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create credentials:
   - Go to "Credentials"
   - Click "Create Credentials"
   - Choose "Desktop Application"
   - Download the credentials file
   - Rename it to `credentials.json` and place in project directory

### 3. Google Sheet Setup
1. Create a new Google Sheet
2. Copy the sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=0
   ```
3. Replace `SPREADSHEET_ID` in `sheets_manager.py`:
```python
SPREADSHEET_ID = 'your-sheet-id'
```
4. Share the sheet with the email in your credentials file

## Running the Application

### Desktop GUI
```bash
python resume_parser.py
```

### Web Interface
```bash
python app.py
```
Then open `http://localhost:5000` in your browser

## Usage

1. Launch the application
2. Click "Upload Resume (PDF)"
3. Select a PDF resume file
4. View the parsed information and ATS score
5. Data will be automatically added to your Google Sheet

## ATS Scoring System

The application scores resumes based on:
- Basic Information (15 points)
- Skills Assessment (25 points)
- Education (20 points)
- Work Experience (25 points)
- Projects and Certifications (15 points)

## File Structure

- `resume_parser.py`: Main application with GUI
- `sheets_manager.py`: Google Sheets integration
- `app.py`: Web interface
- `templates/index.html`: Web interface template

## Troubleshooting

1. If Google Sheets integration fails:
   - Ensure credentials.json is in the project directory
   - Delete token.json if it exists
   - Re-run the application and authenticate

2. If PDF parsing fails:
   - Ensure the PDF is not password protected
   - Check if the PDF is readable/not corrupted

## Contributing

Feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License.
```

This README provides comprehensive setup instructions and should help users get started with the project. Remember to replace placeholder values (API keys, sheet IDs, etc.) with actual values when sharing the code.
