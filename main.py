import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
import jwt
from datetime import datetime, timedelta

from db import init_db, create_user, get_user_hash, verify_password

# Init DB
init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "super_secret_temporary_key_replace_me_in_prod"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=120)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid auth credentials")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid auth credentials")

class SignupRequest(BaseModel):
    username: str
    password: str

@app.post("/api/signup")
async def signup(req: SignupRequest):
    if create_user(req.username, req.password):
        return {"msg": "User created successfully"}
    raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    hashed = get_user_hash(form_data.username)
    if not hashed or not verify_password(form_data.password, hashed):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

def setup_gemini():
    load_dotenv(override=True)
    current_api_key = os.getenv("GEMINI_API_KEY")
    if not current_api_key or current_api_key == "your_gemini_api_key_here":
        raise HTTPException(status_code=500, detail="Gemini API Key is not configured in backend. Please paste it into your .env file and make sure to SAVE the file.")
    genai.configure(api_key=current_api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

class GenerateRequest(BaseModel):
    url: str

prompt_schema = """
Format the output strictly as JSON. No markdown wrappers. Use exactly this schema:
{
    "usp": "The clear USP here...",
    "rsas": [
        {
            "headlines": ["Headline 1", "Headline 2", "Headline 3"],
            "descriptions": ["Description 1", "Description 2"]
        }
    ],
    "displayAds": [
        {
            "concept": "Visual description...",
            "headline": "Ad Headline",
            "copy": "Short text or CTA"
        }
    ]
}"""

@app.post("/api/generate")
async def generate_ads(req: GenerateRequest):
    model = setup_gemini()
    url = req.url
    if not url.startswith('http'):
        url = 'https://' + url

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    for script in soup(["script", "style", "nav", "footer"]):
        script.extract()
    
    text = soup.get_text(separator=' ', strip=True)
    if len(text) > 20000:
        text = text[:20000]

    prompt = f"""
    Analyze the following extracted content from a webpage ({url}):
    "{text}"
    
    Based on this content, please perform the following tasks:
    1. Identify the product's or service's Unique Selling Proposition (USP) in 1-2 clear sentences.
    2. Generate 5 Google Responsive Search Ads (RSAs). For each RSA, provide exactly 3 Headlines (max 30 chars each) and 2 Descriptions (max 90 chars each).
    3. Generate 3 Display Ad Concepts. For each concept, provide a clear visual description, a headline, and a short copy/button text.
    
    {prompt_schema}
    """

    try:
        result = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        return result.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")


@app.post("/api/generate-manual")
async def generate_ads_manual(
    product_name: str = Form(...),
    product_details: str = Form(...),
    custom_usp: str = Form(...),
    file: UploadFile = File(None),
    user: str = Depends(get_current_user)
):
    model = setup_gemini()
    
    contents = []
    text_prompt = f"""
    You are an expert copywriter. The user has provided their own product information:
    - Product Name: {product_name}
    - Details: {product_details}
    - Their Suggested USP: {custom_usp}
    
    Based on these details, AND the provided product image (if any), perform the following tasks:
    1. Synthesize and refine the Unique Selling Proposition (USP) into 1-2 clear, high-converting sentences.
    2. Generate 5 Google Responsive Search Ads (RSAs). For each RSA, provide exactly 3 Headlines (max 30 chars each) and 2 Descriptions (max 90 chars each).
    3. Generate 3 Display Ad Concepts visually inspired by the image. For each concept, provide a clear visual description, a headline, and a short copy/button text.
    
    {prompt_schema}
    """
    contents.append(text_prompt)

    if file:
        image_data = await file.read()
        mime_type = file.content_type
        # fallback if mime isn't set nicely
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg' 
            
        contents.append({
            "mime_type": mime_type,
            "data": image_data
        })

    try:
        result = model.generate_content(
            contents,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        return result.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")


import os as _os
if not _os.path.exists('static'):
    _os.makedirs('static')

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
