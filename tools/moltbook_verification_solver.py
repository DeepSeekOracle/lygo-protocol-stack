"""Solve Moltbook obfuscated math challenges for POST /api/v1/verify."""
from __future__ import annotations

import re

NUM = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}


def _normalize_token(w: str) -> str:
    w = w.lower()
    w = re.sub(r"[^a-z]", "", w)
    fixes = {
        "sixxty": "sixty",
        "thritt": "thirty",
        "thritty": "thirty",
        "fivve": "five",
        "twwo": "two",
        "thre": "three",
        "thre": "three",
        "nooto": "newton",
        "newtons": "newton",
    }
    return fixes.get(w, w)


def _words(text: str) -> list[str]:
    clean = re.sub(r"[^a-zA-Z\s]", " ", text)
    return [_normalize_token(w) for w in clean.split() if re.sub(r"[^a-zA-Z]", "", w)]


def _number_at(words: list[str], i: int) -> int | None:
    if i >= len(words):
        return None
    w = words[i]
    if w in NUM:
        return NUM[w]
    if w.isdigit():
        return int(w)
    if i + 1 < len(words) and f"{w}-{words[i+1]}" in NUM:
        return NUM[f"{w}-{words[i+1]}"]
    if w == "twenty" and i + 1 < len(words) and words[i + 1] in NUM:
        return 20 + NUM[words[i + 1]]
    if w == "thirty" and i + 1 < len(words) and words[i + 1] in NUM:
        return 30 + NUM[words[i + 1]]
    return None


def _parse_spelled_number(words: list[str], start: int) -> tuple[int | None, int]:
    """Return (value, next_index) for sequences like sixty two, thirty three."""
    if start >= len(words):
        return None, start
    w = words[start]
    if w in NUM:
        val = NUM[w]
        nxt = start + 1
        if val in (20, 30, 40, 50, 60, 70, 80, 90) and nxt < len(words) and words[nxt] in NUM and NUM[words[nxt]] < 10:
            return val + NUM[words[nxt]], nxt + 1
        return val, nxt
    return None, start + 1


def _garbled_numbers(low: str) -> list[int]:
    """Pull integers from heavily obfuscated challenge text."""
    found: list[int] = []
    tokens = [
        ("sixty", 60),
        ("seventy", 70),
        ("eighty", 80),
        ("ninety", 90),
        ("thirty", 30),
        ("twenty", 20),
        ("fifty", 50),
        ("forty", 40),
        ("fifteen", 15),
        ("fourteen", 14),
        ("thirteen", 13),
        ("twelve", 12),
        ("eleven", 11),
        ("eight", 8),
        ("seven", 7),
        ("three", 3),
        ("four", 4),
        ("five", 5),
        ("nine", 9),
        ("two", 2),
        ("ten", 10),
        ("six", 6),
    ]
    # compound sixty two before single sixty
    if re.search(r"sixx?ty.{0,12}two", low):
        found.append(62)
    if re.search(r"th[ri]+t?y.{0,12}three", low):
        found.append(33)
    if re.search(r"tw[en]+n?[- ]?t?y.{0,8}fiv", low) or re.search(r"twenty.{0,6}five", low):
        found.append(25)
    elif re.search(r"tw[en]+n?[- ]?t?y", low) and 25 not in found and 20 not in found:
        found.append(20)
    for word, val in tokens:
        if word in low and val not in found:
            # avoid double-counting sixty inside sixty-two
            if word == "sixty" and 62 in found:
                continue
            if word == "thirty" and 33 in found:
                continue
            if word == "two" and 62 in found:
                continue
            if word == "three" and 33 in found:
                continue
            found.append(val)
    return found


def solve_challenge_text(challenge_text: str) -> str | None:
    low = challenge_text.lower()
    garbled = _garbled_numbers(low)
    if len(garbled) >= 2:
        if "newton" in low or "force" in low or "total" in low:
            return f"{garbled[0] + garbled[1]:.2f}"
        if "slow" in low or "speed" in low or "swim" in low:
            return f"{garbled[0] - garbled[1]:.2f}"
        if any(x in low for x in ("minus", "subtract", "less", "lose")):
            return f"{garbled[0] - garbled[1]:.2f}"
        if any(x in low for x in ("times", "multiply", "product")):
            return f"{garbled[0] * garbled[1]:.2f}"
        if any(x in low for x in ("divide", "over", "quotient")):
            return f"{garbled[0] / garbled[1]:.2f}" if garbled[1] else None
        if any(x in low for x in ("plus", "add", "sum", "and")):
            return f"{garbled[0] + garbled[1]:.2f}"
    # Claw / force totals: "sixty two newtons" + "thirty three newtons"
    if "per" in low and "second" in low and ("slow" in low or "speed" in low or "swim" in low):
        words = _words(challenge_text)
        values: list[int] = []
        i = 0
        while i < len(words):
            v, i = _parse_spelled_number(words, i)
            if v is not None:
                values.append(v)
            else:
                i += 1
        if len(values) >= 2:
            return f"{values[0] - values[1]:.2f}"

    if "newton" in low or "force" in low or "claw" in low:
        words = _words(challenge_text)
        values: list[int] = []
        i = 0
        while i < len(words):
            v, i = _parse_spelled_number(words, i)
            if v is not None and v > 0:
                values.append(v)
            else:
                i += 1
        if len(values) >= 2:
            if any(x in low for x in ("total", "sum", "combined", "together", "both")):
                return f"{values[0] + values[1]:.2f}"
            if any(x in low for x in ("difference", "minus", "subtract")):
                return f"{values[0] - values[1]:.2f}"
            return f"{values[0] + values[1]:.2f}"

    words = _words(challenge_text)
    nums: list[tuple[int, int]] = []
    for i in range(len(words)):
        n = _number_at(words, i)
        if n is not None:
            nums.append((i, n))
    if len(nums) < 2:
        return None
    i0, a = nums[0]
    i1, b = nums[1]
    mid = " ".join(words[i0:i1])
    if re.search(r"minus|subtract|slow|less|lose|drop|decrease|fewer", mid):
        return f"{a - b:.2f}"
    if re.search(r"times|multiply|product|multiplied", mid):
        return f"{a * b:.2f}"
    if re.search(r"divide|divided|over|split|quotient", mid):
        return f"{a / b:.2f}" if b else None
    if re.search(r"plus|add|sum|gain|more|increase|and", mid):
        return f"{a + b:.2f}"
    # "slows by" pattern
    if "by" in mid or "slow" in mid:
        return f"{a - b:.2f}"
    return f"{a + b:.2f}"


def submit_verification(session, api_base: str, create_response: dict) -> dict:
    post = create_response.get("post") or create_response.get("data") or {}
    ver = post.get("verification") or create_response.get("verification")
    if not ver:
        status = post.get("verification_status") or post.get("verificationStatus")
        if status in (None, "verified", "passed"):
            return {"ok": True, "skipped": True, "reason": "already_verified_or_not_required"}
        return {"ok": False, "error": "missing_verification_object", "post_id": post.get("id")}

    code = ver.get("verification_code")
    challenge = ver.get("challenge_text") or ""
    answer = solve_challenge_text(challenge)
    if not answer:
        return {"ok": False, "error": "unsolved_challenge", "challenge": challenge, "verification_code": code}

    session.headers["Content-Type"] = "application/json"
    r = session.post(
        f"{api_base}/verify",
        json={"verification_code": code, "answer": answer},
        timeout=30,
    )
    out = {
        "ok": r.ok,
        "http": r.status_code,
        "answer": answer,
        "post_id": post.get("id"),
        "body_preview": r.text[:400],
    }
    try:
        j = r.json()
        out["success"] = j.get("success")
        out["message"] = j.get("message")
        if not j.get("success") and j.get("hint"):
            out["hint"] = j.get("hint")
    except Exception:
        pass
    return out