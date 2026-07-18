import json
import os
import datetime
import anthropic
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ── Tools the agent can use ─────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_todays_disease",
        "description": "Get the disease of the day with symptoms, medicine, potency and dosage",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "call_phone",
        "description": "Call the user's mobile phone and speak a health update to them using AI voice",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The full message to speak on the call. Should be natural spoken language."
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "post_to_facebook",
        "description": "Post today's disease update to the RHCT Facebook page",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "list_all_diseases",
        "description": "List all 31 diseases available in the database",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    }
]


# ── Tool implementations ────────────────────────────────────────────────────

def pick_disease():
    from diseases import DISEASES
    day = datetime.date.today().timetuple().tm_yday
    return DISEASES[(day - 1) % len(DISEASES)]


def tool_get_todays_disease():
    d = pick_disease()
    return {
        "name": d["name"],
        "symptoms": d["symptoms"],
        "medicine": d["medicine"],
        "potency": d["potency"],
        "dosage": d["dosage"],
        "reference": d["reference"]
    }


def tool_call_phone(message: str) -> str:
    try:
        from twilio.rest import Client
        from twilio.twiml.voice_response import VoiceResponse

        sid   = os.environ.get("TWILIO_ACCOUNT_SID")
        token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_ = os.environ.get("TWILIO_PHONE_NUMBER")
        to    = os.environ.get("RECIPIENT_PHONE_NUMBER")

        if not all([sid, token, from_, to]):
            return (
                "Twilio credentials are missing. Please set these in your .env file:\n"
                "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, RECIPIENT_PHONE_NUMBER"
            )

        client = Client(sid, token)
        r = VoiceResponse()
        r.say(message, voice="Polly.Joanna")

        call = client.calls.create(twiml=str(r), to=to, from_=from_)
        return f"Call started! Your phone will ring in a few seconds. (SID: {call.sid})"

    except ImportError:
        return "twilio is not installed. Run: pip install twilio"
    except Exception as e:
        return f"Call failed: {str(e)}"


def tool_post_to_facebook() -> str:
    try:
        page_id = os.environ.get("FB_PAGE_ID")
        token   = os.environ.get("FB_ACCESS_TOKEN")

        if not all([page_id, token]):
            return "Facebook credentials missing. Set FB_PAGE_ID and FB_ACCESS_TOKEN in your .env file."

        d = pick_disease()
        symptoms = "\n".join(f"  • {s}" for s in d["symptoms"])
        post = (
            f"🌿 Disease of the Day: {d['name']}\n\n"
            f"📋 Signs & Symptoms:\n{symptoms}\n\n"
            f"💊 Medicine: {d['medicine']}\n"
            f"⚗️ Potency: {d['potency']}\n"
            f"⏰ Dose: {d['dosage']}\n\n"
            f"🔗 Reference: {d['reference']}\n\n"
            f"{d['tags']}\n\n"
            "⚠️ For educational purposes only. Consult a qualified homeopath."
        )
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/feed",
            data={"message": post, "access_token": token}
        )
        resp.raise_for_status()
        return f"Posted to Facebook successfully! Post ID: {resp.json().get('id')}"

    except Exception as e:
        return f"Facebook post failed: {str(e)}"


def tool_list_all_diseases() -> list:
    from diseases import DISEASES
    return [{"#": i + 1, "disease": d["name"], "medicine": d["medicine"]} for i, d in enumerate(DISEASES)]


def run_tool(name: str, inputs: dict):
    if name == "get_todays_disease":
        return tool_get_todays_disease()
    if name == "call_phone":
        return tool_call_phone(inputs.get("message", ""))
    if name == "post_to_facebook":
        return tool_post_to_facebook()
    if name == "list_all_diseases":
        return tool_list_all_diseases()
    return "Unknown tool"


# ── Agent system prompt ─────────────────────────────────────────────────────

SYSTEM = """You are RHCT Assistant — an intelligent AI health agent for Roheen Homeopathic Care and Treatment, Pakistan.

Your capabilities:
- Tell users about today's disease of the day (symptoms, medicine, potency, dosage)
- Call the user's mobile phone and speak the health update to them by voice
- Post today's update to the RHCT Facebook page
- List all diseases in the database
- Answer general homeopathy questions

Personality:
- Warm, caring, professional
- Speak naturally — not like a robot
- Reply in the same language the user uses (Urdu Roman or English, both fine)
- Keep responses short and to the point

When asked to call: first get today's disease using the tool, build a warm natural-sounding voice message, then make the call.
When making the call message: speak naturally, like a caring doctor's assistant. Start with Assalamu Alaikum."""


# ── Conversation memory (per session) ───────────────────────────────────────

conversation: list = []


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    global conversation

    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"response": "ANTHROPIC_API_KEY not set. Please add it to your .env file and restart."})

    client = anthropic.Anthropic(api_key=api_key)
    conversation.append({"role": "user", "content": user_msg})

    try:
        tool_used = []

        while True:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=SYSTEM,
                tools=TOOLS,
                messages=conversation
            )

            conversation.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                text = "".join(b.text for b in response.content if hasattr(b, "text"))
                return jsonify({"response": text, "tools_used": tool_used})

            if response.stop_reason == "tool_use":
                results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_used.append(block.name)
                        result = run_tool(block.name, block.input)
                        results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                conversation.append({"role": "user", "content": results})

    except Exception as e:
        return jsonify({"response": f"Agent error: {str(e)}"}), 500


@app.route("/clear", methods=["POST"])
def clear():
    global conversation
    conversation = []
    return jsonify({"ok": True})


if __name__ == "__main__":
    # Load .env if present
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    print("\n🌿 RHCT Agent is starting...")
    print("━" * 40)
    print("📍 Open in browser: http://localhost:5000")
    print("━" * 40)
    print("Press Ctrl+C to stop the agent\n")
    app.run(debug=False, port=5000, use_reloader=False)
