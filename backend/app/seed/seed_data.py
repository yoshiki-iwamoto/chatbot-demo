"""Seed script for Hair Salon BLOOM FAQ data.

Run from the backend/ directory:
    python -m app.seed.seed_data
"""

import asyncio

from sqlalchemy import func, select

from app.database import async_session_maker, create_tables
from app.models.faq import FAQ
from app.services.chroma_service import chroma_service

FAQ_DATA: list[dict] = [
    # 営業情報
    {
        "category": "営業情報",
        "question": "営業時間を教えてください",
        "answer": "平日 10:00-20:00 / 土日祝 9:00-19:00 です。",
    },
    {
        "category": "営業情報",
        "question": "定休日はいつですか？",
        "answer": "毎週火曜日が定休日です。",
    },
    {
        "category": "営業情報",
        "question": "住所を教えてください",
        "answer": "東京都渋谷区神宮前3-15-8 BLOOMビル2F です。",
    },
    {
        "category": "営業情報",
        "question": "電話番号を教えてください",
        "answer": "03-6789-0123 です。お気軽にお問い合わせください。",
    },
    {
        "category": "営業情報",
        "question": "最寄駅はどこですか？",
        "answer": "東京メトロ表参道駅 A2出口より徒歩5分です。",
    },
    # メニュー・料金
    {
        "category": "メニュー・料金",
        "question": "カットの料金はいくらですか？",
        "answer": "カットは¥5,500（シャンプー・ブロー込み）です。",
    },
    {
        "category": "メニュー・料金",
        "question": "カラーの料金はいくらですか？",
        "answer": "カット+カラーは¥11,000〜です。髪の長さや薬剤により変動します。",
    },
    {
        "category": "メニュー・料金",
        "question": "パーマの料金はいくらですか？",
        "answer": "カット+パーマは¥13,200〜です。",
    },
    {
        "category": "メニュー・料金",
        "question": "トリートメントの料金はいくらですか？",
        "answer": "トリートメントは¥3,300〜です。",
    },
    {
        "category": "メニュー・料金",
        "question": "ヘッドスパはありますか？",
        "answer": "ヘッドスパは30分¥4,400、60分¥6,600です。",
    },
    {
        "category": "メニュー・料金",
        "question": "前髪カットはいくらですか？",
        "answer": "前髪カットは¥1,100です。",
    },
    # 予約関連
    {
        "category": "予約関連",
        "question": "予約方法を教えてください",
        "answer": "LINE、お電話、ホットペッパービューティーからご予約いただけます。",
    },
    {
        "category": "予約関連",
        "question": "キャンセルポリシーはありますか？",
        "answer": "前日18時までにご連絡ください。当日キャンセルはキャンセル料50%を頂戴しております。",
    },
    {
        "category": "予約関連",
        "question": "当日予約はできますか？",
        "answer": "空きがあれば可能です。LINEまたはお電話にてご確認ください。",
    },
    # その他
    {
        "category": "その他",
        "question": "駐車場はありますか？",
        "answer": "提携駐車場がございます。1時間無料サービス券をお渡ししております。",
    },
    {
        "category": "その他",
        "question": "支払い方法は何がありますか？",
        "answer": "現金、クレジットカード、PayPay、交通系ICがご利用いただけます。",
    },
    {
        "category": "その他",
        "question": "子供連れでも大丈夫ですか？",
        "answer": "キッズスペースがございます。お子様カット（小学生以下）は¥3,300です。",
    },
    {
        "category": "その他",
        "question": "Wi-Fiはありますか？",
        "answer": "無料Wi-Fiをご用意しております。",
    },
]


async def seed():
    print("Creating tables...")
    await create_tables()
    print("Tables ready.")

    async with async_session_maker() as db:
        result = await db.execute(select(func.count(FAQ.id)))
        count = result.scalar() or 0

        if count > 0:
            print(f"FAQs already exist ({count} records). Skipping seed.")
            return

        print(f"Inserting {len(FAQ_DATA)} FAQ records...")
        faqs: list[FAQ] = []
        for item in FAQ_DATA:
            faq = FAQ(
                category=item["category"],
                question=item["question"],
                answer=item["answer"],
            )
            db.add(faq)
            faqs.append(faq)

        await db.commit()

        # Refresh all to get generated IDs
        for faq in faqs:
            await db.refresh(faq)

        print("FAQ records inserted.")

    print("Initializing ChromaDB...")
    chroma_service.initialize()

    print("Syncing FAQs to ChromaDB...")
    for faq in faqs:
        chroma_service.add_faq(faq.id, faq.question, faq.answer, faq.category)
        print(f"  [{faq.category}] {faq.question}")

    print(f"Seed complete. {len(faqs)} FAQs inserted and synced to ChromaDB.")


if __name__ == "__main__":
    asyncio.run(seed())
