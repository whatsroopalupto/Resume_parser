from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from resume_parser import extract_text_from_pdf, extract_info_with_groq, score_resume
from sheets_manager import SheetsManager  # Add this import

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize SheetsManager
sheets_manager = SheetsManager()

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/parse_resume', methods=['POST'])
def parse_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Please upload a PDF file'}), 400

    try:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the resume with error handling
        text = extract_text_from_pdf(filepath)
        if not text:
            return jsonify({'error': 'Failed to extract text from PDF'}), 400

        parsed_data = extract_info_with_groq(text)
        if not parsed_data:
            return jsonify({'error': 'Failed to parse resume data'}), 400

        # Clean up email (remove emojis and extract only valid email)
        if 'email' in parsed_data:
            email = parsed_data['email']
            # First, find the @ symbol position
            at_pos = email.find('@')
            if at_pos != -1:
                # Extract from the character before @ until we find a non-email character
                start = at_pos
                while start > 0 and (email[start-1].isalnum() or email[start-1] in '._-'):
                    start -= 1
                # Extract the rest of the email
                end = at_pos
                while end < len(email) and (email[end].isalnum() or email[end] in '@._-'):
                    end += 1
                parsed_data['email'] = email[start:end]
            else:
                parsed_data['email'] = ''

        # Normalize and round the score
        score = score_resume(parsed_data)
        score = max(0, min(100, round(score)))
        parsed_data["resume_score"] = f"{score}/100"

        # Add to Google Sheets
        if not sheets_manager.add_candidate(parsed_data):
            print("Warning: Failed to add data to Google Sheets")

        # Clean up the uploaded file
        os.remove(filepath)

        return jsonify(parsed_data)

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)