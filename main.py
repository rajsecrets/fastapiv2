from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import base64 
import requests 
from PIL import Image 
from io import BytesIO 
import fitz  # PyMuPDF 
import os 
import uvicorn
from typing import Dict, Any, Optional
 
app = FastAPI(title="Document Processing API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
 
# Configuration 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash" 
DOCUMENT_TYPES = ["Land Records", "Caste Certificates", "Property Registrations"] 
 
# Encode uploaded file to base64 
async def encode_file(uploaded_file: UploadFile) -> Optional[str]: 
    """ 
    Encode the uploaded file to a base64 string. 
    Supports PDFs and images. 
    """ 
    file_bytes = await uploaded_file.read() 
     
    try:
        if uploaded_file.content_type == "application/pdf": 
            pdf = fitz.open(stream=BytesIO(file_bytes)) 
            page = pdf[0] 
            pix = page.get_pixmap() 
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples) 
        elif uploaded_file.content_type.startswith('image/'): 
            img = Image.open(BytesIO(file_bytes)) 
        else: 
            return None 
     
        img_byte_arr = BytesIO() 
        img.save(img_byte_arr, format='JPEG') 
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
 
# Query Gemini API 
def query_gemini(prompt: str, image_b64: Optional[str] = None) -> str: 
    """ 
    Send a request to the Gemini API and return its response. 
    """ 
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable not set")
        
    url = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}" 
    parts = [{"text": prompt}] 
     
    if image_b64: 
        parts.append({ 
            "inline_data": { 
                "mime_type": "image/jpeg", 
                "data": image_b64 
            } 
        }) 
     
    try:
        response = requests.post( 
            url, 
            json={"contents": [{"parts": parts}]}, 
            headers={"Content-Type": "application/json"}, 
            timeout=30 
        ) 
         
        if response.status_code != 200: 
            return f"API request failed: {response.status_code}" 
         
        data = response.json() 
        return data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No response')
    except Exception as e:
        return f"Error querying Gemini API: {str(e)}" 
 
@app.post("/process-document/", response_model=Dict[str, Any])
async def process_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """ 
    Process the uploaded document: 
      - Encodes the file. 
      - Classifies the document. 
      - Extracts important details. 
      - Verifies authenticity. 
    Returns a dictionary with results. 
    """ 
    try:
        image_b64 = await encode_file(file) 
        if not image_b64: 
            raise HTTPException(status_code=400, detail="Unsupported file format")
    
        # Query for classification 
        classify_prompt = f"Classify this document into: {', '.join(DOCUMENT_TYPES)}" 
        doc_type = query_gemini(classify_prompt, image_b64) 
    
        # Query for details extraction 
        extract_prompt = "Extract and organize important details (Names, Dates, ID numbers, Locations, Key terms)." 
        details = query_gemini(extract_prompt, image_b64) 
    
        # Query for authenticity verification 
        verify_prompt = "Analyze for tampering or forgery signs." 
        verification = query_gemini(verify_prompt, image_b64) 
    
        return { 
            "type": doc_type, 
            "details": details, 
            "verification": verification
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "online", "message": "Document Processing API is running"}

if __name__ == "__main__":
    # This is used when running locally
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
