import os
import time
import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

print("[INFO] Loading Iris dataset...")
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)

print("[INFO] Training RandomForest model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("[INFO] Evaluating model...")
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"[INFO] Model Accuracy: {accuracy:.2f}")

# --- SAVE THE MODEL ---
os.makedirs("model", exist_ok=True)   # ensure folder exists
model_path = os.path.join("model", "random_forest_model.pkl")
joblib.dump(model, model_path)

print(f"[INFO] Model saved at: {model_path}")
time.sleep(1)
print("[INFO] Training completed successfully.")