from surya.detection import DetectionPredictor
from surya.recognition import RecognitionPredictor
from surya.foundation import FoundationPredictor
from PIL import Image

try:
    print("Initializing FoundationPredictor...")
    foundation_predictor = FoundationPredictor()
    print("Initializing DetectionPredictor...")
    det_predictor = DetectionPredictor()
    print("Initializing RecognitionPredictor...")
    rec_predictor = RecognitionPredictor(foundation_predictor)
    print("Surya initialized successfully!")
except Exception as e:
    print(f"Surya initialization failed: {e}")
