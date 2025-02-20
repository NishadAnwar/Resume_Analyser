from fastapi import FastAPI, File, UploadFile
import pdfminer.high_level
import docx
import openai  # or google.generativeai for Gemini
import json
import os

app = FastAPI()

# Configure AI API (Choose Gemini or OpenAI)
USE_GEMINI = False  # Set True for Gemini, False for OpenAI

if USE_GEMINI:
    import google.generativeai as genai
    genai.configure(api_key="YOUR_GEMINI_API_KEY")
else:
    openai.api_key = "YOUR_OPENAI_API_KEY"

# Function to extract text from a PDF
def extract_text_from_pdf(file_path):
    with open(file_path, "rb") as f:
        return pdfminer.high_level.extract_text(f)

# Function to extract text from a DOCX
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

# Resume Analysis Function using AI API
def analyze_resume(text):
    prompt = f"""
    Analyze the following resume and extract structured information:
    {text}

    Provide a JSON output with:
    - name
    - email
    - phone
    - core_skills
    - soft_skills
    - experience
    - education
    - resume_rating (1-10)
    - improvement_areas
    - upskill_suggestions
    """

    if USE_GEMINI:
        response = genai.generate_text(model="gemini-pro", prompt=prompt)
        return json.loads(response.text)
    else:
        response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a resume analyzer. Extract key skills, experience, and suggest improvements."},
        {"role": "user", "content": prompt}
    ]
)

        return json.loads(response["choices"][0]["message"]["content"])

# API to handle file upload and analysis
@app.post("/upload/")
async def upload_resume(file: UploadFile = File(...)):
    file_ext = file.filename.split(".")[-1]
    file_path = f"uploads/{file.filename}"
    
    # Save the uploaded file
    os.makedirs("uploads", exist_ok=True)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Extract text from the file
    extracted_text = ""
    if file_ext == "pdf":
        extracted_text = extract_text_from_pdf(file_path)
    elif file_ext in ["docx", "doc"]:
        extracted_text = extract_text_from_docx(file_path)
    else:
        return {"error": "Unsupported file format. Please upload a PDF or DOCX file."}

    # AI-based resume analysis
    result = analyze_resume(extracted_text)
    
    return result
