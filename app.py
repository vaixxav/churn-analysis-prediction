import os
import joblib
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "churn_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "models", "feature_names.pkl")
REPORT_PATH = os.path.join(BASE_DIR, "reports", "model_comparison.csv")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
feature_names = joblib.load(FEATURES_PATH)

NUMERIC_COLUMNS = ["SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges"]

# Columns that were label-mapped to 0/1 in training (not one-hot encoded)
BINARY_MAP = {
    "gender": {"Female": 0, "Male": 1},
    "Partner": {"No": 0, "Yes": 1},
    "Dependents": {"No": 0, "Yes": 1},
    "PhoneService": {"No": 0, "Yes": 1},
    "PaperlessBilling": {"No": 0, "Yes": 1},
}

# Categorical columns that were one-hot encoded with drop_first=True.
# The value listed first for each column is the dropped/reference category
# (all dummy columns stay 0 when the form submits that value).
ONE_HOT_COLUMNS = {
    "MultipleLines": ["No", "No phone service", "Yes"],
    "InternetService": ["DSL", "Fiber optic", "No"],
    "OnlineSecurity": ["No", "No internet service", "Yes"],
    "OnlineBackup": ["No", "No internet service", "Yes"],
    "DeviceProtection": ["No", "No internet service", "Yes"],
    "TechSupport": ["No", "No internet service", "Yes"],
    "StreamingTV": ["No", "No internet service", "Yes"],
    "StreamingMovies": ["No", "No internet service", "Yes"],
    "Contract": ["Month-to-month", "One year", "Two year"],
    "PaymentMethod": [
        "Bank transfer (automatic)",
        "Credit card (automatic)",
        "Electronic check",
        "Mailed check",
    ],
}

FORM_FIELDS = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "tenure",
    "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
    "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV",
    "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod",
    "MonthlyCharges", "TotalCharges",
]


def build_feature_row(form):
    """Turn raw form input into the same 30-column layout the model was trained on."""
    row = {col: 0 for col in feature_names}

    # Binary label-encoded columns
    for col, mapping in BINARY_MAP.items():
        row[col] = mapping[form[col]]

    # SeniorCitizen already arrives as 0/1
    row["SeniorCitizen"] = int(form["SeniorCitizen"])

    # Numeric columns
    row["tenure"] = float(form["tenure"])
    row["MonthlyCharges"] = float(form["MonthlyCharges"])
    row["TotalCharges"] = float(form["TotalCharges"])

    # One-hot encoded columns (drop_first=True -> first listed category is the baseline)
    for col, categories in ONE_HOT_COLUMNS.items():
        value = form[col]
        if value != categories[0]:
            dummy_col = f"{col}_{value}"
            if dummy_col in row:
                row[dummy_col] = 1

    df_row = pd.DataFrame([row], columns=feature_names)
    df_row[NUMERIC_COLUMNS] = scaler.transform(df_row[NUMERIC_COLUMNS])
    return df_row


def risk_bucket(probability):
    if probability >= 0.6:
        return "High", "coral"
    if probability >= 0.3:
        return "Medium", "amber"
    return "Low", "teal"


def build_recommendations(form, probability):
    """Small rule-based nudge engine — flags the levers that most commonly drive churn."""
    tips = []
    if form["Contract"] == "Month-to-month":
        tips.append("On a month-to-month contract — offering a 1-year term with a small discount tends to cut churn risk fast.")
    if form["InternetService"] == "Fiber optic" and form["PaymentMethod"] == "Electronic check":
        tips.append("Fiber + electronic check is the highest-risk combination in this dataset — worth a retention call.")
    if form["TechSupport"] == "No" and form["InternetService"] != "No":
        tips.append("No tech support add-on — bundling free support for a trial period often improves stickiness.")
    if float(form["tenure"]) < 12:
        tips.append("Still early in the customer lifecycle (under a year) — this is when churn risk is naturally highest.")
    if form["OnlineSecurity"] == "No" and form["InternetService"] != "No":
        tips.append("No online security add-on — bundling it can raise perceived value at low cost.")
    if not tips:
        if probability < 0.3:
            tips.append("No major risk flags — this customer profile looks stable.")
        else:
            tips.append("Risk is elevated but doesn't match a single obvious lever — consider a general loyalty offer.")
    return tips


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return render_template("predict.html", result=None, form_values=None)

    form = {field: request.form.get(field, "") for field in FORM_FIELDS}

    try:
        features = build_feature_row(form)
        probability = float(model.predict_proba(features)[0][1])
        prediction = "Yes" if probability >= 0.5 else "No"
        level, tone = risk_bucket(probability)
        recommendations = build_recommendations(form, probability)

        result = {
            "prediction": prediction,
            "probability": round(probability * 100, 1),
            "level": level,
            "tone": tone,
            "recommendations": recommendations,
        }
    except (ValueError, KeyError) as exc:
        result = {"error": f"Couldn't read that input — {exc}"}

    return render_template("predict.html", result=result, form_values=form)


@app.route("/insights")
def insights():
    rows = []
    if os.path.exists(REPORT_PATH):
        df = pd.read_csv(REPORT_PATH)
        df = df.sort_values(by="Accuracy", ascending=False)
        rows = df.round(4).to_dict(orient="records")
    return render_template("insights.html", rows=rows)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True)
