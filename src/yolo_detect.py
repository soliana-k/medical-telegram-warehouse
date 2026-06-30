import os
import glob
import pandas as pd
from ultralytics import YOLO

IMAGE_DIR = "data/raw/images"
OUTPUT_CSV = "data/yolo_detection_results.csv"

def classify_image(detected_objects):
   
    product_classes = {'bottle', 'cup', 'box', 'bowl', 'can', 'handbag', 'cell phone'}
    has_person = 'person' in detected_objects
    has_product = any(obj in product_classes for obj in detected_objects)
    
    if has_person and has_product:
        return "promotional"
    elif has_product and not has_person:
        return "product_display"
    elif has_person and not has_product:
        return "lifestyle"
    else:
        return "other"

def run_object_detection():
    print("Loading YOLOv8 nano model...")
    model = YOLO("yolov8n.pt")
    image_paths = glob.glob(os.path.join(IMAGE_DIR, "**", "*.jpg"), recursive=True)
    if not image_paths:
        print(f"No target images found in path: {IMAGE_DIR}")
        return

    print(f"Found {len(image_paths)} images to analyze. Starting detection pipeline...")
    
    detection_records = []

    for path in image_paths:
        
        normalized_path = os.path.normpath(path)
        path_parts = normalized_path.split(os.sep)
        
        channel_name = path_parts[-2]
        message_id_str = path_parts[-1].replace(".jpg", "")
        
        try:
            message_id = int(message_id_str)
        except ValueError:
            continue 
         
        results = model(path, verbose=False)[0]
        
       
        detected_objects = []
        highest_confidence = 0.0
        
        for box in results.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            confidence = float(box.conf[0])
            
            detected_objects.append(class_name)
            if confidence > highest_confidence:
                highest_confidence = confidence

    
        image_category = classify_image(detected_objects)
        objects_string = ", ".join(set(detected_objects)) if detected_objects else "none"
        
        detection_records.append({
            "message_id": message_id,
            "channel_name": channel_name,
            "detected_objects": objects_string,
            "confidence_score": round(highest_confidence, 4) if highest_confidence > 0 else 0.0,
            "image_category": image_category,
            "image_path": path
        })

    df = pd.DataFrame(detection_records)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Inference complete! Results saved cleanly to {OUTPUT_CSV}")

if __name__ == "__main__":
    run_object_detection()