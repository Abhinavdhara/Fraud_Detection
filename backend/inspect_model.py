import joblib
pipeline = joblib.load("model/fraud_detection_pipeline.pkl")


print("🔍 Loaded type:", type(pipeline))
print("📄 Contents:", pipeline)
