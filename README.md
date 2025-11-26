# Body Measurement Estimator

A Python application that estimates body measurements from photos using computer vision and pose detection. Upload photos of yourself, provide your height, and get estimated measurements for chest, waist, hips, inseam, and arm length.

## Features

- **Multiple Input Methods**: Web interface and command-line interface
- **Pose Detection**: Uses MediaPipe for accurate body landmark detection
- **Multi-View Support**: Accepts front, side, and back view images for improved accuracy
- **Automatic Scaling**: Calibrates measurements using your provided height
- **Confidence Scoring**: Each measurement includes a confidence score
- **Privacy-Focused**: Images are processed in-memory and not stored

## How It Works

1. **Pose Detection**: MediaPipe detects body landmarks (shoulders, hips, knees, etc.)
2. **Scale Calibration**: Your height is used to convert pixel measurements to real-world units
3. **Measurement Estimation**: Body measurements are calculated from landmark distances
4. **Multi-View Fusion**: If multiple images are provided, measurements are averaged with confidence weighting

## Installation

### Prerequisites

- Python 3.11+
- pip or uv package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or if using uv:

```bash
uv sync
```

## Usage

### Web Interface (Recommended)

1. Start the server:

```bash
python main.py
```

2. Open your browser to `http://localhost:5000`
3. Upload your images and enter your height
4. View your estimated measurements with confidence scores

### Command Line Interface

```bash
python measure.py --images front.jpg side.jpg --height-cm 175
```

Or using inches:

```bash
python measure.py --images front.jpg --height-inches 69 --output results.json
```

**Options:**
- `--images`: One or more image file paths (required)
- `--height-cm`: Your height in centimeters
- `--height-inches`: Your height in inches (alternative to --height-cm)
- `--output`: Save results to JSON file (optional, prints to stdout if omitted)

## API Endpoints

### POST /api/measure

Upload images and get measurements.

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `images`: One or more image files (JPG/PNG)
  - `height_cm`: Height in centimeters (optional if height_inches provided)
  - `height_inches`: Height in inches (optional if height_cm provided)

**Response:**

```json
{
  "height_cm": 175.0,
  "measurements": {
    "chest_cm": {
      "value": 96.5,
      "confidence": 0.87
    },
    "waist_cm": {
      "value": 78.2,
      "confidence": 0.85
    },
    "hips_cm": {
      "value": 98.0,
      "confidence": 0.83
    },
    "inseam_cm": {
      "value": 78.0,
      "confidence": 0.70
    },
    "left_arm_cm": {
      "value": 60.2,
      "confidence": 0.80
    }
  },
  "used_images": ["front.jpg", "side.jpg"],
  "warnings": []
}
```

### GET /health

Health check endpoint.

## Photo Guidelines

For best results:

1. **Stand straight** with arms slightly away from body
2. **Wear fitted clothing** (tight-fitting works best)
3. **Good lighting** with minimal shadows
4. **Plain background** with minimal clutter
5. **Full body visible** from head to feet
6. **Multiple angles**: Take front, side, and optionally back views
7. **Camera at chest height** positioned 6-10 feet away

## Measurements Provided

- **Chest/Bust**: Circumference around the fullest part of the chest
- **Waist**: Circumference at the natural waistline
- **Hips**: Circumference around the fullest part of the hips
- **Inseam**: Length from crotch to ankle
- **Arm Length**: Length from shoulder to wrist (left and right)

## Accuracy & Limitations

**Expected Accuracy:**
- Under ideal conditions: ±2-5 cm
- Depends on: image quality, pose accuracy, clothing fit, and body type

**Limitations:**
- Estimates only - not a substitute for professional measurements
- Less accurate with loose clothing or obscured body parts
- Requires clear, well-lit photos with full body visible
- May be less accurate for certain body types or poses

**Important:** For critical applications (tailoring, medical purposes), use professional measurements.

## Privacy & Ethics

- **No Storage**: Images are processed in-memory and immediately discarded
- **No Identification**: No personally identifying information is collected or stored
- **User Consent**: Always obtain consent before processing photos
- **Transparency**: Users are informed about limitations and expected accuracy

## Project Structure

```
.
├── main.py                 # FastAPI web server
├── measure.py             # CLI interface
├── src/
│   ├── pose_detector.py   # MediaPipe pose detection
│   ├── measurement_engine.py  # Measurement calculation logic
│   ├── processor.py       # Image processing pipeline
│   └── models.py          # Pydantic data models
├── static/
│   ├── index.html         # Web interface
│   ├── style.css          # Styling
│   └── app.js             # Frontend JavaScript
└── README.md
```

## Technology Stack

- **FastAPI**: Web framework
- **MediaPipe**: Pose detection and landmark extraction
- **OpenCV**: Image processing
- **NumPy**: Numerical computations
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

## Development

Run in development mode with auto-reload:

```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## License

This project is provided as-is for educational and personal use.

## Disclaimer

This tool provides estimates based on computer vision. Results may vary based on image quality, pose, clothing, and body type. For critical applications requiring precise measurements (medical, professional tailoring), please consult a professional.