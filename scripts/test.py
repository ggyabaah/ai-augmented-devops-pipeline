import os
import joblib
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

print("[INFO] Loading Iris dataset...")
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)

# --- LOAD THE MODEL ---
model_path = os.path.join("model", "random_forest_model.pkl")

if not os.path.exists(model_path):
    raise FileNotFoundError(f"[ERROR] Trained model not found at {model_path}. Run train.py first.")

print(f"[INFO] Loading model from {model_path}...")
model = joblib.load(model_path)

print("[INFO] Evaluating model...")
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"[INFO] Model Accuracy (Test Script): {accuracy:.2f}")
print("[INFO] Test completed successfully.")