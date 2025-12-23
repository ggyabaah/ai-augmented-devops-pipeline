# scripts/tester_logic.py
import os
import joblib
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

def evaluate_model(model_path: str, test_size: float = 0.2, random_state: int = 42) -> float:
    """
    Pure function style: load model, run evaluation, return accuracy.
    Raises FileNotFoundError if model missing.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")

    model = joblib.load(model_path)

    iris = load_iris()
    _, X_test, _, y_test = train_test_split(
        iris.data, iris.target, test_size=test_size, random_state=random_state
    )

    acc = accuracy_score(y_test, model.predict(X_test))
    return float(acc)