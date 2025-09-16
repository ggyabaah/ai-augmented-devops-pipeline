import os
import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

print("[INFO] Training and saving model (quick save)...")

iris = load_iris()
X, y = iris.data, iris.target

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

model_dir = os.path.join(os.path.dirname(__file__), "..", "model")
os.makedirs(model_dir, exist_ok=True)

model_path = os.path.join(model_dir, "random_forest_model.pkl")
joblib.dump(model, model_path)

print(f"[INFO] Model saved at: {model_path}")