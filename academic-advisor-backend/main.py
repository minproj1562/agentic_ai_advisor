from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from PyPDF2 import PdfReader
import firebase_admin
from firebase_admin import credentials, storage
import os
import io
from datetime import datetime
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load environment variables (optional, for production)
# from dotenv import load_dotenv
# load_dotenv()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        cred_path = os.getenv("FIREBASE_CRED_PATH", r"C:\Users\Sharon Shalom\miniproj2\academic-advisor-backend\serviceAccountKey.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'academic-advisor-6ed1a.appspot.com'
        })
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        raise

# CORS configuration (updated to match frontend port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Add both ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 for token-based authentication (optional, for security)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    # Validate token (implement Firebase token verification here)
    # For now, assume token contains uid
    return token.split('.')[0]  # Placeholder; replace with real validation

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

@app.post("/parse-cv")
async def parse_cv(
    cv: UploadFile = File(...),
    uid: str = Form(...),
    authorization: Optional[str] = Header(None),
    current_user: str = Depends(get_current_user)
):
    # Validate file type
    if cv.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size
    cv_size = await cv.seek(0, os.SEEK_END)
    await cv.seek(0)  # Reset pointer
    if cv_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")

    # Validate uid (basic check; enhance with token validation)
    if uid != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized: UID mismatch")

    # Read and parse PDF
    try:
        pdf_content = await cv.read()
        pdf = PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""

        # Basic parsing (placeholder; enhance with NLP)
        expertise = {"raw_text": text[:500]}  # Limit to 500 chars for demo

        # Upload to Firebase Storage
        bucket = storage.bucket()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"cvs/{uid}/{timestamp}_{cv.filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(pdf_content, content_type="application/pdf")

        # Generate signed URL instead of making public
        url = blob.generate_signed_url(
            expiration=datetime(2025, 12, 31),  # Adjust expiration as needed
            method="GET"
        )

        logger.info(f"CV uploaded for uid {uid}: {url}")
        return {
            "message": "CV uploaded and parsed successfully",
            "uid": uid,
            "cv_url": url,
            "expertise": expertise,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"CV processing failed for uid {uid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CV processing failed: {str(e)}")

@app.get("/")
async def read_root():
    return {"message": "Backend is running", "status": "ok", "time": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)