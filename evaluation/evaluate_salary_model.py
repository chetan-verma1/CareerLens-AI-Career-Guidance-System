import os
import math
import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(BASE_DIR, "data", "salary_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model", "salary_model.pkl")


def main():
    if not os.path.exists(DATA_PATH):
        print("salary_data.csv not found.")
        return

    if not os.path.exists(MODEL_PATH):
        print("salary_model.pkl not found.")
        return

    df = pd.read_csv(DATA_PATH)

    required_columns = ["Role", "Experience_Years", "Salary_LPA"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        return

    df = df.dropna(subset=required_columns)

    X = df[["Role", "Experience_Years"]]
    y = df["Salary_LPA"]

    if len(df) < 5:
        print("Not enough salary records for evaluation.")
        return

    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = joblib.load(MODEL_PATH)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\nSalary Model Evaluation")
    print("-----------------------")
    print(f"Total records: {len(df)}")
    print(f"Test records: {len(X_test)}")
    print(f"MAE: {mae:.2f} LPA")
    print(f"RMSE: {rmse:.2f} LPA")
    print(f"R2 Score: {r2:.4f}")


if __name__ == "__main__":
    main()