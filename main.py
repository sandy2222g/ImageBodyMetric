from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import uvicorn
from src.processor import ImageProcessor
from src.models import MeasurementResponse, EnhancedMeasurementResponse

app = FastAPI(title="Body Measurement Estimator", version="2.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

processor = ImageProcessor()


@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with open("static/dashboard.html", "r") as f:
        return f.read()


@app.post("/api/measure", response_model=MeasurementResponse)
async def measure(
    images: List[UploadFile] = File(...),
    height_cm: Optional[float] = Form(None),
    height_inches: Optional[float] = Form(None),
    gender: Optional[str] = Form(None)
):
    if not images:
        raise HTTPException(status_code=400, detail="At least one image is required")
    
    if height_cm is None and height_inches is None:
        raise HTTPException(status_code=400, detail="Height must be provided in cm or inches")
    
    if height_cm is None and height_inches is not None:
        height_cm = height_inches * 2.54
    
    if height_cm <= 0 or height_cm > 300:
        raise HTTPException(status_code=400, detail="Height must be between 0 and 300 cm")
    
    try:
        image_bytes = []
        image_names = []
        
        for image in images:
            content = await image.read()
            
            if not content:
                continue
            
            if not image.content_type or not image.content_type.startswith('image/'):
                continue
                
            image_bytes.append(content)
            image_names.append(image.filename or "unknown")
        
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No valid images provided")
        
        result = processor.process_images(image_bytes, image_names, height_cm, gender)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/api/measure/enhanced", response_model=EnhancedMeasurementResponse)
async def measure_enhanced(
    images: List[UploadFile] = File(...),
    height_cm: Optional[float] = Form(None),
    height_inches: Optional[float] = Form(None),
    gender: Optional[str] = Form(None)
):
    """
    Enhanced measurement endpoint with detailed image analysis,
    multi-view fusion, and accuracy rating.
    """
    if not images:
        raise HTTPException(status_code=400, detail="At least one image is required")
    
    if height_cm is None and height_inches is None:
        raise HTTPException(status_code=400, detail="Height must be provided in cm or inches")
    
    if height_cm is None and height_inches is not None:
        height_cm = height_inches * 2.54
    
    if height_cm <= 0 or height_cm > 300:
        raise HTTPException(status_code=400, detail="Height must be between 0 and 300 cm")
    
    try:
        image_bytes = []
        image_names = []
        
        for image in images:
            content = await image.read()
            
            if not content:
                continue
            
            if not image.content_type or not image.content_type.startswith('image/'):
                continue
                
            image_bytes.append(content)
            image_names.append(image.filename or "unknown")
        
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No valid images provided")
        
        result = processor.process_images_enhanced(
            image_bytes, image_names, height_cm, gender
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
