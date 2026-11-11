"""DigiMath Instagram publisher.
Modes:  am     -> 8 feed posts (with captions) + 8 question stories   (10:00 Baku)
        pm     -> 8 solution stories, then move to the next day         (18:00 Baku)
        check  -> test the token and show how many days of content are left (posts nothing)
Uses only the official Instagram API (graph.instagram.com) and the Python standard library.
"""
import json, os, sys, time, glob, urllib.request, urllib.parse, urllib.error

API = "https://graph.facebook.com/" + os.environ.get("IG_API_VERSION", "v23.0")  # Facebook Login (Unified login) token
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
USER = os.environ.get("IG_USER_ID", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/content"
STATE_FILE = "state.json"
LOW_CONTENT_DAYS = 3


def http(method, url, params=None):
    data = urllib.parse.urlencode(params or {}).encode()
    if method == "GET":
        url, data = url + ("&" if "?" in url else "?") + data.decode(), None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Instagram API error {e.code}: {e.read().decode()[:500]}")


def wait_ready(cid):
    for _ in range(60):
        st = http("GET", f"{API}/{cid}", {"fields": "status_code", "access_token": TOKEN}).get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise SystemExit(f"Container {cid} failed: {st}")
        time.sleep(5)
    raise SystemExit(f"Container {cid} not ready after 5 minutes")


def publish(image_url, caption=None, story=False):
    p = {"image_url": image_url, "access_token": TOKEN}
    if story:
        p["media_type"] = "STORIES"
    else:
        p["caption"] = caption or ""
    cid = http("POST", f"{API}/{USER}/media", p)["id"]
    wait_ready(cid)
    mid = http("POST", f"{API}/{USER}/media_publish", {"creation_id": cid, "access_token": TOKEN})["id"]
    print(f"  published {'story' if story else 'post'}: {image_url.rsplit('/', 1)[-1]} -> {mid}")
    time.sleep(3)


def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {"day": 1, "done": [], "log": []}


def save_state(s):
    json.dump(s, open(STATE_FILE, "w"), indent=2, ensure_ascii=False)


def days_left(s):
    return len([d for d in glob.glob("content/day_*") if int(d.rsplit("_", 1)[-1]) >= s["day"]])


def warn_low_content(s):
    left = days_left(s)
    if left > LOW_CONTENT_DAYS or s.get("warned_at_day") == s["day"] or not REPO:
        return
    body = (f"Sual bankında cəmi {left} günlük material qalıb (növbəti gün: {s['day']}).\n\n"
            "Claude-a yazın: \"növbəti həftənin suallarını hazırla\". Hazır zip faylını reponun inbox/ qovluğuna yükləyin.")
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues", method="POST",
                                 data=json.dumps({"title": f"DigiMath: {left} günlük sual qalıb", "body": body}).encode(),
                                 headers={"Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN', '')}",
                                          "Accept": "application/vnd.github+json"})
    try:
        urllib.request.urlopen(req, timeout=30)
        s["warned_at_day"] = s["day"]
        print(f"Low-content warning issue created ({left} days left).")
    except Exception as e:
        print("Could not create warning issue:", e)


def run(mode):
    s = load_state()
    d = f"content/day_{s['day']:03d}"
    if mode == "check":
        me = http("GET", f"{API}/{USER}", {"fields": "username,media_count", "access_token": TOKEN})
        print("Token OK:", me)
        print(f"Next day: {s['day']}  |  days of content left: {days_left(s)}")
        return
    if not os.path.exists(f"{d}/manifest.json"):
        raise SystemExit(f"No content for day {s['day']} ({d}). Upload a new question pack to inbox/.")
    items = json.load(open(f"{d}/manifest.json"))
    url = lambda f: f"{RAW}/day_{s['day']:03d}/{f}"
    if mode == "am":
        for it in items:  # stories play in order Q1 -> Q8
            key = f"am{it['n']}"
            if key not in s["done"]:
                publish(url(it["story_am"]), story=True); s["done"].append(key); save_state(s)
    elif mode == "pm":
        if not any(k.startswith("am") for k in s["done"]):
            raise SystemExit("Morning posts of this day were not published; solutions skipped.")
        for it in items:
            key = f"pm{it['n']}"
            if key not in s["done"]:
                publish(url(it["story_pm"]), story=True); s["done"].append(key); save_state(s)
        s["log"] = (s.get("log", []) + [f"day {s['day']} completed {time.strftime('%Y-%m-%d')}"])[-60:]
        s["day"] += 1
        s["done"] = []
        save_state(s)
        warn_low_content(s)
        save_state(s)
    else:
        raise SystemExit(f"Unknown mode {mode}")


if __name__ == "__main__":
    if not TOKEN or not USER:
        raise SystemExit("IG_ACCESS_TOKEN / IG_USER_ID secrets are missing.")
    run(sys.argv[1] if len(sys.argv) > 1 else "check")
