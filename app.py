from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import re

app = Flask(__name__)
CORS(app)   # ✅ APPLY HERE

# Load trained model
model = joblib.load("model.pkl")
# --- FEATURE FUNCTIONS ---
def get_length(url):
    return len(str(url))

def count_dots(url):
    return str(url).count('.')

def has_at_symbol(url):
    return 1 if '@' in str(url) else 0

def has_ip(url):
    pattern = r'(([01]?\d\d?|2[0-4]\d|25[0-5])\.){3}([01]?\d\d?|2[0-4]\d|25[0-5])'
    return 1 if re.search(pattern, str(url)) else 0

def count_hyphen(url):
    return str(url).count('-')

def count_slash(url):
    return str(url).count('/')

def check_https(url):
    return 0 if str(url).lower().startswith("https") else 1

def count_digits(url):
    return sum(c.isdigit() for c in str(url))

def is_shortened(url):
    match = re.search(r'bit\.ly|goo\.gl|tinyurl|t\.co|ow\.ly|is\.gd|buff\.ly|adf\.ly', str(url))
    return 1 if match else 0

# --- PREDICTION FUNCTION ---
def predict_url(url):
    url = url.lower().strip()
    url = url.replace('\n', '').replace('\r', '')
    url = url.replace("www.", "")
    if url.endswith('/'):
        url = url[:-1]

    features = {
        'url_length': get_length(url),
        'dot_count': count_dots(url),
        'has_at': has_at_symbol(url),
        'has_ip': has_ip(url),
        'hyphen_count': count_hyphen(url),
        'slash_count': count_slash(url),
        'has_https': check_https(url),
        'digit_count': count_digits(url),
        'is_shortened': is_shortened(url),
    }

    features_df = pd.DataFrame([features])
    prob = model.predict_proba(features_df)[0][1]

    if prob > 0.4:
        return "phishing", round(prob, 2)
    else:
        return "legitimate", round(1 - prob, 2)

# --- API ---
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    url = data.get("url")

    prediction, confidence = predict_url(url)

    return jsonify({
        "prediction": prediction,
        "confidence": confidence
    })

if __name__ == "__main__":
    app.run(debug=True)

