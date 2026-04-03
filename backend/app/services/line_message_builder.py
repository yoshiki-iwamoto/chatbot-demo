from linebot.v3.messaging import (
    ButtonsTemplate,
    CarouselColumn,
    CarouselTemplate,
    MessageAction,
    TemplateMessage,
    TextMessage,
    URIAction,
)


def build_booking_message() -> list:
    """Build a rich booking message with buttons for reservation."""
    return [
        TemplateMessage(
            alt_text="ご予約",
            template=ButtonsTemplate(
                title="ご予約",
                text="オンラインからご予約いただけます。",
                actions=[
                    URIAction(
                        label="予約ページへ",
                        uri="https://example.com/reserve",
                    ),
                    MessageAction(
                        label="電話で予約",
                        text="電話番号を教えてください",
                    ),
                ],
            ),
        )
    ]


def build_menu_carousel() -> list:
    """Build a carousel message showing salon menu items."""
    columns = [
        CarouselColumn(
            thumbnail_image_url="https://placehold.co/800x600/d4a574/fff?text=Cut",
            title="カット",
            text="¥5,500〜",
            actions=[URIAction(label="詳しく見る", uri="https://example.com/menu")],
        ),
        CarouselColumn(
            thumbnail_image_url="https://placehold.co/800x600/c9a96e/fff?text=Color",
            title="カラー",
            text="¥11,000〜",
            actions=[URIAction(label="詳しく見る", uri="https://example.com/menu")],
        ),
        CarouselColumn(
            thumbnail_image_url="https://placehold.co/800x600/8b6f5e/fff?text=Perm",
            title="パーマ",
            text="¥13,200〜",
            actions=[URIAction(label="詳しく見る", uri="https://example.com/menu")],
        ),
        CarouselColumn(
            thumbnail_image_url="https://placehold.co/800x600/5c4033/fff?text=Treatment",
            title="トリートメント",
            text="¥3,300〜",
            actions=[URIAction(label="詳しく見る", uri="https://example.com/menu")],
        ),
    ]
    return [
        TemplateMessage(
            alt_text="メニュー一覧",
            template=CarouselTemplate(columns=columns),
        )
    ]


def build_access_message() -> list:
    """Build a text message with salon location and access information."""
    return [
        TextMessage(
            text=(
                "\U0001F4CD Hair Salon BLOOM\n"
                "東京都渋谷区神宮前3-15-8 BLOOMビル2F\n"
                "\n"
                "\U0001F6B6 東京メトロ表参道駅 A2出口より徒歩5分\n"
                "\U0001F4DE 03-6789-0123\n"
                "\n"
                "\U0001F4CD Google Maps:\n"
                "https://maps.google.com/?q=東京都渋谷区神宮前3-15-8"
            )
        )
    ]
