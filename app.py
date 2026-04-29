import os
from flask import Flask, render_template, request, jsonify
from main import HealthcareChatbot  # your existing logic

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATASET_PATH = os.path.join(BASE_DIR, "symptoms_dataset.csv")

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

print("BASE_DIR:", BASE_DIR)
print("Templates dir exists:", os.path.isdir(TEMPLATES_DIR))
if os.path.isdir(TEMPLATES_DIR):
    print("templates files:", os.listdir(TEMPLATES_DIR))
print("Static dir exists:", os.path.isdir(STATIC_DIR))
if os.path.isdir(STATIC_DIR):
    print("static files:", os.listdir(STATIC_DIR))
print("Dataset exists:", os.path.isfile(DATASET_PATH))

bot = HealthcareChatbot(dataset_path=DATASET_PATH)


@app.route("/")
def index():
    return render_template("index.html", bot_name=bot.name)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    cmd = user_message.lower()
    if cmd in {"exit", "quit", "bye"}:
        reply = "Goodbye! If you need more help, reopen the chat."
    elif cmd == "help":
        reply = (
            "Example symptoms you can mention:\n"
            "fever, cough, sore throat, headache, stomach pain,\n"
            "nausea, diarrhea, chest pain, shortness of breath,\n"
            "dizziness, fatigue, rash, etc."
        )
    elif any(greet in cmd for greet in ["hi", "hello", "hey"]):
        reply = "Hello! Tell me your symptoms, or type 'help'."
    else:
        reply = bot.analyze_symptoms(user_message)

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
