from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import joblib
import pandas as pd
import re
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

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

# --- 4 NEW FEATURE FUNCTIONS ---
def get_domain(url):
    try:
        return urlparse(str(url)).netloc
    except:
        return ""

def domain_length(url):
    try:
        return len(get_domain(url))
    except:
        return 0

def subdomain_count(url):
    try:
        domain = get_domain(url)
        return domain.count('.')
    except:
        return 0

def has_suspicious_words(url):
    keywords = ['login', 'verify', 'bank', 'secure', 'account', 'update']
    return 1 if any(word in url.lower() for word in keywords) else 0

def suspicious_tld(url):
    tlds = ['.xyz', '.tk', '.ml', '.ga', '.cf']
    return 1 if any(tld in url.lower() for tld in tlds) else 0

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
        'domain_length': domain_length(url),
        'subdomain_count': subdomain_count(url),
        'has_suspicious_words': has_suspicious_words(url),
        'suspicious_tld': suspicious_tld(url),
    }

    features_df = pd.DataFrame([features])
    prob = model.predict_proba(features_df)[0][1]

    if prob > 0.4:
        return "phishing", round(prob, 2)
    else:
        return "legitimate", round(1 - prob, 2)

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    prediction, confidence = predict_url(url)

    return jsonify({
        "prediction": prediction,
        "confidence": confidence
    })

if __name__ == "__main__":
    app.run(debug=True)