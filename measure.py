#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from src.processor import ImageProcessor


def main():
    parser = argparse.ArgumentParser(description='Body Measurement Estimator CLI')
    parser.add_argument('--images', nargs='+', required=True, help='Paths to image files')
    parser.add_argument('--height-cm', type=float, help='Height in centimeters')
    parser.add_argument('--height-inches', type=float, help='Height in inches')
    parser.add_argument('--output', help='Output JSON file (optional, prints to stdout if not specified)')
    
    args = parser.parse_args()
    
    if args.height_cm is None and args.height_inches is None:
        print("Error: Either --height-cm or --height-inches must be provided", file=sys.stderr)
        sys.exit(1)
    
    height_cm = args.height_cm if args.height_cm else args.height_inches * 2.54
    
    if height_cm <= 0 or height_cm > 300:
        print("Error: Height must be between 0 and 300 cm", file=sys.stderr)
        sys.exit(1)
    
    image_bytes = []
    image_names = []
    
    for img_path in args.images:
        path = Path(img_path)
        if not path.exists():
            print(f"Warning: Image not found: {img_path}", file=sys.stderr)
            continue
        
        try:
            with open(path, 'rb') as f:
                image_bytes.append(f.read())
                image_names.append(path.name)
        except Exception as e:
            print(f"Warning: Could not read {img_path}: {e}", file=sys.stderr)
            continue
    
    if not image_bytes:
        print("Error: No valid images could be loaded", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing {len(image_bytes)} image(s)...", file=sys.stderr)
    
    processor = ImageProcessor()
    result = processor.process_images(image_bytes, image_names, height_cm)
    
    result_dict = result.model_dump()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result_dict, f, indent=2)
        print(f"Results saved to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result_dict, indent=2))


if __name__ == "__main__":
    main()
