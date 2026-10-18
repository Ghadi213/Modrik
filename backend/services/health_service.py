import subprocess
import requests
from services.chat_service import generate_chat_reply
from services.states import get_users_count
import time


last_gemini_check = None
last_gemini_status = "unknown"


# Check OpenCRAVAT
def check_opencravat():
    try:
        subprocess.run(["oc", "version"], capture_output=True, timeout=3)
        return "stable"
    except Exception:
        return "down"


# Check PanelApp API
def check_panelapp():
    try:
        r = requests.get(
            "https://panelapp.genomicsengland.co.uk/api/v1/panels/",
            timeout=3
        )
        return "stable" if r.status_code == 200 else "unstable"
    except Exception:
        return "down"


# Check Gemini API
def check_gemini():

    global last_gemini_check
    global last_gemini_status

    if (
        last_gemini_check is not None
        and time.time() - last_gemini_check < 300
    ):
        return last_gemini_status

    try:

        test_reply = generate_chat_reply(
            messages=[
                {
                    "role": "user",
                    "content": "ping"
                }
            ],
            analysis_summary=None
        )

        if test_reply and test_reply.strip():
            last_gemini_status = "stable"
        else:
            last_gemini_status = "unstable"

    except Exception as e:

        print("Gemini Health Check Error:", e)

        last_gemini_status = "down"

    last_gemini_check = time.time()

    return last_gemini_status


# System Health
def get_system_health():
    return {
        "opencravat": check_opencravat(),
        "panelapp": check_panelapp(),
        "gemini": check_gemini(),
        "total_users": get_users_count()
    }

