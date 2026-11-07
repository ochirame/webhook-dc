"""Kirim quote / trivia / meme random ke Discord lewat webhook.

Env:
  DISCORD_FUN_WEBHOOK_URL  (wajib) URL webhook, simpen di GitHub Secrets
  MODE                 random | quote | trivia | meme  (default: random)
"""
import html
import json
import os
import random
import sys
import urllib.request

WEBHOOK = os.environ.get("DISCORD_FUN_WEBHOOK_URL", "").strip()
MODE = os.environ.get("MODE", "random").strip().lower()

# Discord (Cloudflare) sering nolak User-Agent default urllib, jadi set sendiri
UA = "discord-fun-drop/1.0 (+github-actions)"


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def make_quote():
    d = get_json("https://zenquotes.io/api/random")[0]
    return {
        "title": "💬 Quote of the day",
        "description": f"“{d['q']}”\n\n— **{d['a']}**",
        "color": 0x5865F2,
    }


def make_trivia():
    d = get_json("https://opentdb.com/api.php?amount=1&type=multiple")["results"][0]
    question = html.unescape(d["question"])
    correct = html.unescape(d["correct_answer"])
    options = [html.unescape(x) for x in d["incorrect_answers"]] + [correct]
    random.shuffle(options)
    letters = "ABCD"
    opts_text = "\n".join(f"**{letters[i]}.** {o}" for i, o in enumerate(options))
    answer = f"{letters[options.index(correct)]}. {correct}"
    return {
        "title": "🧠 Trivia time!",
        "description": f"**{question}**\n\n{opts_text}",
        "color": 0xFEE75C,
        "fields": [{"name": "Jawaban (klik buat buka)", "value": f"||{answer}||"}],
        "footer": {"text": f"{html.unescape(d['category'])} • {d['difficulty']}"},
    }


def make_meme():
    # coba beberapa kali, skip meme NSFW/spoiler
    for _ in range(5):
        d = get_json("https://meme-api.com/gimme")
        if d.get("nsfw") or d.get("spoiler") or not d.get("url"):
            continue
        return {
            "title": d.get("title", "Meme")[:256],
            "url": d.get("postLink"),
            "image": {"url": d["url"]},
            "color": 0xEB459E,
            "footer": {"text": f"r/{d.get('subreddit', '?')} • 👍 {d.get('ups', 0)}"},
        }
    raise RuntimeError("Gagal dapet meme yang aman")


GENERATORS = {"quote": make_quote, "trivia": make_trivia, "meme": make_meme}


def post(embed):
    payload = json.dumps({"username": "Fun Drop", "embeds": [embed]}).encode()
    req = urllib.request.Request(
        WEBHOOK,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": UA},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        print(f"Terkirim, status {r.status}")


def main():
    if not WEBHOOK:
        sys.exit("DISCORD_FUN_WEBHOOK_URL belum di-set")

    if MODE == "random":
        order = list(GENERATORS)
        random.shuffle(order)  # kalo satu sumber error, coba yang lain
    elif MODE in GENERATORS:
        order = [MODE]
    else:
        sys.exit(f"MODE tidak dikenal: {MODE}")

    for name in order:
        try:
            embed = GENERATORS[name]()
            post(embed)
            print(f"Jenis: {name}")
            return
        except Exception as e:  # noqa: BLE001
            print(f"[{name}] gagal: {e}", file=sys.stderr)

    sys.exit("Semua sumber gagal")


if __name__ == "__main__":
    main()
