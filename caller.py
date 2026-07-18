import os
import datetime
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Pause
from diseases import DISEASES


def pick_disease() -> dict:
    day_of_year = datetime.date.today().timetuple().tm_yday
    return DISEASES[(day_of_year - 1) % len(DISEASES)]


def build_twiml(disease: dict) -> str:
    r = VoiceResponse()

    r.say(
        "Assalamu Alaikum! Good morning. "
        "This is your daily update from R H C T, Roheen Homeopathic Care and Treatment.",
        voice="Polly.Joanna"
    )
    r.pause(length=1)

    r.say(f"Today's disease of the day is: {disease['name']}.", voice="Polly.Joanna")
    r.pause(length=1)

    r.say("Signs and Symptoms:", voice="Polly.Joanna")
    for symptom in disease["symptoms"]:
        r.say(f"  {symptom}.", voice="Polly.Joanna")
        r.pause(length=1)

    r.pause(length=1)
    r.say(f"Recommended Homeopathic Medicine: {disease['medicine']}.", voice="Polly.Joanna")
    r.say(f"Potency: {disease['potency']}.", voice="Polly.Joanna")
    r.say(f"Dosage: {disease['dosage']}.", voice="Polly.Joanna")

    r.pause(length=2)
    r.say(
        "Please note: this information is for educational purposes only. "
        "Always consult a qualified homeopath before taking any medicine.",
        voice="Polly.Joanna"
    )
    r.pause(length=1)
    r.say("Have a healthy and blessed day. Allah Hafiz!", voice="Polly.Joanna")

    return str(r)


def make_call(twiml: str) -> str:
    client = Client(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"]
    )
    call = client.calls.create(
        twiml=twiml,
        to=os.environ["RECIPIENT_PHONE_NUMBER"],   # your mobile e.g. +923001234567
        from_=os.environ["TWILIO_PHONE_NUMBER"]    # your Twilio number
    )
    return call.sid


if __name__ == "__main__":
    disease = pick_disease()

    print(f"\n📞 Today's disease: {disease['name']}")
    print(f"💊 Medicine: {disease['medicine']} | {disease['potency']}")
    print(f"⏰ Dosage: {disease['dosage']}\n")

    twiml = build_twiml(disease)

    if os.environ.get("TWILIO_ACCOUNT_SID"):
        sid = make_call(twiml)
        print(f"✅ Call started! SID: {sid}")
    else:
        print("⚠️  Twilio credentials not set. Running in preview mode.")
        print("\n--- TwiML Script (what the agent will say) ---")
        print(twiml)
