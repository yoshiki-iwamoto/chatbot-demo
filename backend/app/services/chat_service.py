import re

KEYWORD_PATTERNS: dict[str, re.Pattern] = {
    "booking": re.compile(r"予約|予約したい|予約する", re.IGNORECASE),
    "menu": re.compile(r"メニュー|料金|価格", re.IGNORECASE),
    "access": re.compile(r"アクセス|場所|行き方", re.IGNORECASE),
}

WEB_KEYWORD_RESPONSES: dict[str, dict] = {
    "booking": {
        "reply": (
            "ご予約ありがとうございます！\n"
            "下記URLからご希望の日時をお選びください。\n"
            "https://example.com/reserve\n"
            "\nお電話でも承っております（03-6789-0123）"
        ),
        "reply_type": "text",
        "quick_replies": ["メニューを見る", "アクセス", "営業時間"],
    },
    "menu": {
        "reply": (
            "当店のメニューと料金はこちらです：\n\n"
            "\U0001F487 カット: ¥5,500〜\n"
            "\U0001F3A8 カラー: ¥11,000〜\n"
            "\U0001F4AB パーマ: ¥13,200〜\n"
            "\u2728 トリートメント: ¥3,300〜\n\n"
            "詳しくはこちら: https://example.com/menu"
        ),
        "reply_type": "text",
        "quick_replies": ["予約する", "アクセス", "営業時間"],
    },
    "access": {
        "reply": (
            "\U0001F4CD Hair Salon BLOOM\n"
            "東京都渋谷区神宮前3-15-8 BLOOMビル2F\n\n"
            "\U0001F6B6 東京メトロ表参道駅 A2出口より徒歩5分\n"
            "\U0001F4DE 03-6789-0123\n\n"
            "\U0001F4CD Google Maps:\n"
            "https://maps.google.com/?q=東京都渋谷区神宮前3-15-8"
        ),
        "reply_type": "text",
        "quick_replies": ["メニューを見る", "予約する", "営業時間"],
    },
}


def match_keyword(text: str) -> str | None:
    """Match text against keyword patterns. Returns keyword key or None."""
    for key, pattern in KEYWORD_PATTERNS.items():
        if pattern.search(text):
            return key
    return None


def get_web_keyword_response(keyword: str) -> dict | None:
    """Get a web-friendly response for a keyword. Returns None if keyword unknown."""
    return WEB_KEYWORD_RESPONSES.get(keyword)
