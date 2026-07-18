import os
import datetime
import requests
from diseases import DISEASES


def build_post(disease: dict) -> str:
    symptoms = "\n".join(f"  • {s}" for s in disease["symptoms"])
    post = (
        f"🌿 Disease of the Day: {disease['name']}\n\n"
        f"📋 Signs & Symptoms:\n{symptoms}\n\n"
        f"💊 Homeopathic Medicine: {disease['medicine']}\n"
        f"⚗️ Potency: {disease['potency']}\n"
        f"⏰ Dose: {disease['dosage']}\n\n"
        f"🔗 Reference: {disease['reference']}\n\n"
        f"{disease['tags']}\n\n"
        f"⚠️ For educational purposes only. Always consult a qualified homeopath before taking any medicine."
    )
    return post


def post_to_facebook(message: str) -> dict:
    page_id = os.environ["FB_PAGE_ID"]
    access_token = os.environ["FB_ACCESS_TOKEN"]
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    response = requests.post(url, data={"message": message, "access_token": access_token})
    response.raise_for_status()
    return response.json()


def pick_disease() -> dict:
    # Cycle through diseases based on day of year so each day gets a different one
    day_of_year = datetime.date.today().timetuple().tm_yday
    index = (day_of_year - 1) % len(DISEASES)
    return DISEASES[index]


if __name__ == "__main__":
    disease = pick_disease()
    post = build_post(disease)

    print("=" * 60)
    print("POST PREVIEW:")
    print("=" * 60)
    print(post)
    print("=" * 60)

    if os.environ.get("FB_PAGE_ID") and os.environ.get("FB_ACCESS_TOKEN"):
        result = post_to_facebook(post)
        print(f"✅ Posted successfully! Post ID: {result.get('id')}")
    else:
        print("⚠️  FB_PAGE_ID or FB_ACCESS_TOKEN not set — skipping actual post (preview only).")
