import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk  # Add this line to import ttk
import os
import requests
from PyPDF2 import PdfReader
import json

# ----------- Groq API Config ------------
GROQ_API_KEY = "ENTER YOUR API KEY"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"

# ----------- PDF Text Extractor ------------
def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            try:
                # Extract text using PyPDF2
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            except Exception as page_error:
                print(f"Error extracting text from page: {page_error}")
                continue
                
        # Check if any text was extracted
        if not text.strip():
            print("No text could be extracted from the PDF.")
            return ""
            
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return ""

def extract_info_with_groq(resume_text):
    # Clean up email addresses in the text before sending to API
    import re
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, resume_text)
    for email in emails:
        # Ensure no unwanted prefixes are present
        clean_email = re.sub(r'\bpe([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1', email)
        resume_text = resume_text.replace(email, clean_email)

    prompt = f"""
You are an intelligent resume parser. Extract the following structured JSON fields from the resume text provided:
- name
- email (extract ONLY the actual email address, format: user@domain.com)
- phone
- skills (as a list)
- education (as a list of entries, each entry with:
    - institution
    - degree
    - graduation
    - percentage (if available)
    - cgpa (if available, on a scale of 10 or 4)
    - year
)
- work_experience (as a list of entries, each entry with:
    - company
    - role
    - duration
    - responsibilities (as a list)
)
- certifications (as a list)
- projects (as a list of entries, each entry with:
    - name
    - description
    - technologies_used (as a list)
)

Ensure to extract both percentage and CGPA if available in the education details.
Only return the JSON data and nothing else.

Resume Text:
\"\"\"
{resume_text}
\"\"\"
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a resume parser that must extract clean data. For email addresses, never include emojis or special characters, only extract the raw email in format user@domain.com"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1  # Reduced temperature for more consistent output
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status()

    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    return json.loads(reply)

# ----------- Resume Scoring Logic ------------
def score_resume(parsed_data):
    # Set random seed for consistency
    score = 0
    detailed_scores = {}

    # Basic Information (15 points) - More strict validation
    basic_info_score = 0
    if parsed_data.get("name") and len(parsed_data["name"].split()) >= 2:
        basic_info_score += 5
    
    # Improved email validation
    email = parsed_data.get("email", "")
    email = ''.join(char for char in email if ord(char) < 128).strip()  # Remove emojis
    if email and "@" in email and "." in email.split("@")[1]:
        basic_info_score += 5
    
    # Improved phone validation
    if parsed_data.get("phone"):
        digits = ''.join(filter(str.isdigit, parsed_data["phone"]))
        if len(digits) >= 10:
            basic_info_score += 5

    detailed_scores["basic_information"] = basic_info_score
    score += basic_info_score

    # Skills Assessment (25 points)
    skills_score = 0
    skills = parsed_data.get("skills", [])
    if isinstance(skills, list):
        # Points for number of skills
        if len(skills) >= 8:
            skills_score += 15
        elif len(skills) >= 5:
            skills_score += 10
        elif len(skills) >= 3:
            skills_score += 5
        
        # Points for technical skills
        technical_keywords = {"python", "java", "javascript", "sql", "aws", "docker", "kubernetes", "react", "angular", "node"}
        tech_skill_count = sum(1 for skill in skills if skill.lower() in technical_keywords)
        skills_score += min(tech_skill_count * 2, 10)  # Max 10 points for technical skills
    detailed_scores["skills"] = skills_score
    score += skills_score

    # Education (20 points)
    education_score = 0
    education = parsed_data.get("education", [])
    if isinstance(education, list):
        # Points for number of degrees
        education_score += min(len(education) * 5, 10)
        
        # Points for education details
        for edu in education:
            if isinstance(edu, dict):
                try:
                    # Check for percentage
                    percentage = float(str(edu.get("percentage", "0")).replace('%', ''))
                    if percentage >= 80:
                        education_score += 3
                    elif percentage >= 70:
                        education_score += 2

                    # Check for CGPA
                    cgpa = edu.get("cgpa", 0)
                    if isinstance(cgpa, (int, float)):
                        if cgpa >= 8 or cgpa >= 3.5:  # Handling both 10 and 4 point scales
                            education_score += 3
                        elif cgpa >= 7 or cgpa >= 3.0:
                            education_score += 2
                except (ValueError, TypeError):
                    continue

    detailed_scores["education"] = min(education_score, 20)  # Cap at 20
    score += min(education_score, 20)

    # Work Experience (25 points)
    experience_score = 0
    work_experience = parsed_data.get("work_experience", [])
    if isinstance(work_experience, list):
        # Points for number of experiences
        experience_score += min(len(work_experience) * 5, 15)
        
        # Points for duration and roles
        for exp in work_experience:
            if isinstance(exp, dict):
                if "duration" in exp:
                    # Add points for experience duration
                    duration = exp["duration"].lower()
                    if "year" in duration:
                        years = int(''.join(filter(str.isdigit, duration)))
                        experience_score += min(years * 2, 10)
    detailed_scores["work_experience"] = min(experience_score, 25)  # Cap at 25
    score += min(experience_score, 25)

    # Projects and Certifications (15 points)
    extra_score = 0
    projects = parsed_data.get("projects", [])
    certifications = parsed_data.get("certifications", [])
    
    if isinstance(projects, list):
        extra_score += min(len(projects) * 3, 8)  # Max 8 points for projects
    
    if isinstance(certifications, list):
        extra_score += min(len(certifications) * 2, 7)  # Max 7 points for certifications
    
    detailed_scores["projects_certifications"] = extra_score
    score += extra_score

    # Add detailed scores to parsed_data
    parsed_data["detailed_scores"] = detailed_scores
    parsed_data["total_score"] = score
    parsed_data["ats_recommendation"] = get_ats_recommendation(score)

    return score

def get_ats_recommendation(score):
    if score >= 85:
        return "Strong Match - Highly Recommended"
    elif score >= 70:
        return "Good Match - Recommended"
    elif score >= 60:
        return "Potential Match - Consider for Review"
    else:
        return "Weak Match - May Need Improvement"

# ----------- GUI Application ------------
# Add at the top with other imports
from sheets_manager import SheetsManager

class ResumeParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Resume Parser with Groq AI")
        self.sheets_manager = SheetsManager()  # Initialize sheets manager
        self.root.geometry("800x600")

        # Add status label
        self.status_label = tk.Label(root, text="", fg="blue")
        self.status_label.pack(pady=5)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')

        self.resume_tab = tk.Frame(self.notebook)
        self.notebook.add(self.resume_tab, text='Resume Data')

        self.output_box = scrolledtext.ScrolledText(self.resume_tab, wrap=tk.WORD, width=100, height=30)
        self.output_box.pack(padx=10, pady=10)

        self.export_tab = tk.Frame(self.notebook)
        self.notebook.add(self.export_tab, text='Export')

        tk.Button(self.export_tab, text="Export to File", command=self.export_to_file).pack(pady=5)

        tk.Button(root, text="Upload Resume (PDF)", command=self.upload_resume).pack(pady=10)

    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update()

    def upload_resume(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not filepath:
            return

        try:
            self.update_status("Reading PDF file...")
            text = extract_text_from_pdf(filepath)
            if not text.strip():
                messagebox.showerror("Error", "Could not extract text from PDF")
                self.update_status("")
                return

            self.update_status("Analyzing resume...")
            parsed_data = extract_info_with_groq(text)
            
            self.update_status("Calculating score...")
            score = score_resume(parsed_data)
            parsed_data["resume_score"] = f"{score}/100"

            # Add to Google Sheets with visual confirmation
            self.update_status("Adding to Google Sheets...")
            if self.sheets_manager.add_candidate(parsed_data):
                messagebox.showinfo("Success", "Resume data added to Google Sheets successfully!")
            else:
                messagebox.showerror("Error", "Failed to add data to Google Sheets")

            pretty_output = json.dumps(parsed_data, indent=2)
            self.output_box.delete(1.0, tk.END)
            self.output_box.insert(tk.END, pretty_output)

            self.last_output = pretty_output
            self.update_status("Analysis complete!")
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror("API Error", "Failed to connect to Groq API. Please check your internet connection.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Failed to parse API response")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
        finally:
            self.update_status("")

    def export_to_file(self):
        if hasattr(self, "last_output"):
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.last_output)
                messagebox.showinfo("Success", "Output exported successfully.")

# ----------- Run the App ------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ResumeParserApp(root)
    root.mainloop()
