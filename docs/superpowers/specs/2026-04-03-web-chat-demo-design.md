# Web Chat Demo Page - Design Spec

## Overview

LINE AIチャットボット（Hair Salon BLOOM）にブラウザで体験できるWebチャットデモページを追加する。
ポートフォリオの最重要ページとして、クラウドワークス/ランサーズの応募文にURLを貼り、発注者がクリックするだけでAIチャットを体験可能にする。

## Architecture

```
demo-site/ (静的HTML/CSS/JS) ──POST /api/web-chat──▶ backend/ (FastAPI)
                                                        │
                                                   chat_service.py
                                                   ┌────┴────┐
                                              keyword判定  rag_service.py
                                              (共通ロジック)   (+ 会話履歴)
                                                        │
                                                   ChatHistory DB
                                                   (user_id = web_xxx)
```

## 1. Backend Changes

### 1.1 New: `backend/app/services/chat_service.py`

共通サービス層。`line_handler.py` からキーワード判定ロジックを抽出。

```python
# 責務:
# - キーワードパターン判定（予約/メニュー/アクセス）
# - Web向けテキスト+URL応答生成
# - RAG応答生成（会話履歴付き）
# - quick_replies の決定

KEYWORD_PATTERNS: dict[str, re.Pattern]  # line_handler.pyから移動

def match_keyword(text: str) -> Optional[str]
    """テキストからキーワードを判定。ヒットしたキー名またはNone。"""

def get_web_keyword_response(keyword: str) -> dict
    """キーワードに対応するWeb向けレスポンスを返す。
    Returns: {"reply": str, "reply_type": "text", "quick_replies": list[str]}
    """

async def generate_web_reply(message: str, session_id: str, db: AsyncSession) -> dict
    """Webチャット用の統合応答メソッド。
    1. キーワード判定 → ヒットならget_web_keyword_response()
    2. DBから直近5往復の会話履歴を取得
    3. rag_service.generate_answer(message, history) でRAG応答
    4. ユーザーメッセージ＋ボット応答をDBに保存
    5. レスポンスdict返却
    """
```

#### Web向けキーワード応答の変換

| keyword | 応答内容 |
|---------|---------|
| booking | 「ご予約ありがとうございます！下記URLからご希望の日時をお選びください。\nhttps://example.com/reserve\nお電話でも承っております（03-6789-0123）」quick_replies: ["メニューを見る", "アクセス", "営業時間"] |
| menu | 「当店のメニューと料金はこちらです：\n\n💇 カット: ¥4,400〜\n🎨 カラー: ¥6,600〜\n💫 パーマ: ¥7,700〜\n✨ トリートメント: ¥3,300〜\n\n詳しくはこちら: https://example.com/menu」quick_replies: ["予約する", "アクセス", "営業時間"] |
| access | 既存のTextMessage内容をそのまま使用。quick_replies: ["メニューを見る", "予約する", "営業時間"] |

### 1.2 New: `backend/app/routers/web_chat.py`

```
POST /api/web-chat
```

#### Request Schema
```json
{
  "message": "予約したいのですが",
  "session_id": "web_xxxxxxxxxxxx"
}
```

#### Response Schema
```json
{
  "reply": "ご予約ありがとうございます！...",
  "reply_type": "text",
  "quick_replies": ["メニューを見る", "アクセス", "営業時間"]
}
```

#### Validation
- `message`: 1〜500文字
- `session_id`: `web_` プレフィックス必須、20文字以内

#### Rate Limiting
- インメモリ `dict[session_id → list[datetime]]` で管理
- 同一session_idから1分間に10リクエスト超で HTTP 429
- 古いタイムスタンプは自動クリーンアップ

### 1.3 Modify: `backend/app/services/rag_service.py`

`generate_answer()` メソッドを拡張して会話履歴を受け取れるようにする。

```python
async def generate_answer(self, user_message: str, history: list[dict] | None = None) -> str:
    # 1. ChromaDB検索（変更なし）
    # 2. system promptビルド（変更なし）
    # 3. messages構築:
    #    - system prompt
    #    - history（直近5往復、あれば）: [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}, ...]
    #    - 今回のuser message
    # 4. LLM API呼び出し
```

既存のLINE webhook呼び出し（historyなし）は `history=None` で後方互換。

### 1.4 Modify: `backend/app/services/line_handler.py`

`KEYWORD_PATTERNS` と判定ロジックを `chat_service.py` に移動し、`match_keyword()` をインポートして使用。LINE専用テンプレートビルダー（`line_message_builder.py`）の呼び出しはそのまま残す。

### 1.5 Modify: `backend/app/main.py`

- `web_chat` ルーターを登録: `app.include_router(web_chat_router, prefix="/api")`
- CORS origins に demo-site のオリジンを追加可能にする（`.env` の `CORS_ORIGINS` に追記）

### 1.6 Session & History

既存の `ChatHistory` モデル（`user_id`, `message_type`, `content`, `timestamp`）をそのまま利用。
- `user_id` に `web_xxxx` のsession_idを格納
- LINE（`U` プレフィックス）とWeb（`web_` プレフィックス）が同一テーブルで共存
- 管理画面のチャット履歴画面からもWebユーザーの会話が確認可能

## 2. Demo Site: `demo-site/`

### 2.1 Directory Structure

```
demo-site/
├── index.html               # ランディングページ
├── chat.html                # Webチャットデモ（最重要）
├── css/
│   └── style.css            # 全ページ共通スタイル
├── js/
│   ├── chat.js              # チャットUI制御
│   └── api.js               # API通信
└── assets/
    ├── salon-logo.svg       # サロンロゴ
    ├── bot-avatar.svg       # ボットアイコン
    └── og-image.png         # OGP画像（プレースホルダー）
```

### 2.2 chat.html - Webチャットデモページ（最重要）

#### Layout
- PC: 2カラム（左=説明テキスト、右=チャットエリア）
- スマホ: チャットエリア全幅、説明テキストは上部に折りたたみ

#### Chat Area Specs
- 最大幅: 420px
- 高さ: 80vh（最大700px）
- 背景色: #E8E4DC（LINE風ベージュ）
- 角丸: 16px、ボックスシャドウあり

#### Bubble Specs
- ボット（左寄せ）: 白 #FFFFFF、左上にbot-avatar.svg、角丸12px
- ユーザー（右寄せ）: 緑 #8CE28C（LINE風）、角丸12px
- タイムスタンプ: HH:MM形式、グレー小文字
- アニメーション: スライドアップ + フェードイン

#### Input Area
- 白背景入力フィールド + 緑の送信ボタン
- Enter=送信、Shift+Enter=改行
- 送信中: 入力無効化 + 「...」タイピングインジケーター

#### Quick Replies
- 初期表示: 「メニューを見る」「予約する」「アクセス」「営業時間」
- タップで該当テキストをユーザーメッセージとして送信
- ボット応答ごとに応答内容に応じたボタンを更新

#### Initial State
- ページ表示時にボットから自動メッセージ（APIなし）:
  「こんにちは！Hair Salon BLOOMです💐\nカット、カラー、パーマなどのメニューや、ご予約についてお気軽にお聞きください！」
- クイックリプライ4つ表示

#### PC Side Panel（チャットエリア左側）
- 「このデモについて」の説明
- 「実際のLINEでも試せます →」+ QRコード（プレースホルダー）
- 「管理画面はこちら →」+ URL
- 「導入についてのご相談 →」+ URL（プレースホルダー）

### 2.3 index.html - ランディングページ

#### Sections（上から順に）
1. **Header**: サロンロゴ + 「AI Chat Demo」バッジ、ナビ（チャットを試す/管理画面/導入について）
2. **Hero**: キャッチコピー「LINEに届いたお客様の質問に、AIが24時間お答えします」+ CTA「今すぐチャットを試す →」
3. **Features**: 3カード横並び（AI自然文回答 / LINE対応 / 管理画面FAQ編集）
4. **Screenshots**: 左=LINE実機（プレースホルダー）、右=管理画面（プレースホルダー）
5. **Steps**: 導入5ステップ + 「最短3日で導入可能」
6. **Pricing**: ライト ¥50,000〜 / スタンダード ¥150,000〜 / プレミアム ¥300,000〜 + 「※デモ用の参考価格」
7. **CTA**: 「導入のご相談」+ チャットお試しボタン
8. **Footer**: 「Demo by Yoshi」+ GitHub link

#### Design
- フォント: Noto Sans JP (Google Fonts)
- カラー: プライマリ #8B7355、アクセント #C9A96E、背景 #FAFAF5、テキスト #333
- レスポンシブ（モバイルファースト）
- スクロールフェードインアニメーション（IntersectionObserver）

### 2.4 js/api.js

```javascript
const API_BASE_URL = '';  // 相対パス（プロキシ経由）

async function sendMessage(message, sessionId) {
    // POST /api/web-chat
    // エラーハンドリング: 429 → レート制限メッセージ、500 → 通信エラー
    // Returns: { reply, reply_type, quick_replies }
}
```

### 2.5 js/chat.js

```javascript
// Session management
// - 初回: "web_" + 16桁ランダム生成、localStorage保存
// - 再訪: localStorage から復元
// - 24h経過: リセット

// Core functions
function initChat()           // 初期メッセージ+クイックリプライ表示
function sendUserMessage(text) // ユーザー吹き出し描画→API送信→ボット応答描画
function addBubble(type, text) // 吹き出しDOM生成（アニメーション付き）
function showTypingIndicator() // 「...」表示
function hideTypingIndicator() // 「...」非表示
function addQuickReplies(replies) // ボタン描画
function scrollToBottom()      // 自動スクロール

// Event listeners
// - 送信ボタンクリック
// - Enter キー（Shift+Enterは改行）
// - クイックリプライボタンクリック（イベント委譲）
```

### 2.6 SVG Assets

#### salon-logo.svg
花モチーフのシンプルなサロンロゴ。カラー: #8B7355 + #C9A96E。

#### bot-avatar.svg
丸い背景にロボットアイコン。カラー: #8B7355。

### 2.7 OGP

両HTMLの `<head>` に設定:
- `og:title`: 「LINE AIチャットボット デモ | Hair Salon BLOOM」
- `og:description`: 「AIがお客様の質問に24時間自動応答。LINEに届いたメッセージにAIが回答するチャットボットのデモです。」
- `og:image`: `assets/og-image.png`
- `og:type`: `website`

## 3. Modified Files Summary

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/chat_service.py` | **New** | 共通キーワード判定 + Web応答生成 |
| `backend/app/routers/web_chat.py` | **New** | POST /api/web-chat エンドポイント |
| `backend/app/services/rag_service.py` | **Modify** | generate_answer() に history パラメータ追加 |
| `backend/app/services/line_handler.py` | **Modify** | キーワード判定を chat_service.py からインポート |
| `backend/app/main.py` | **Modify** | web_chat ルーター登録 |
| `demo-site/index.html` | **New** | ランディングページ |
| `demo-site/chat.html` | **New** | Webチャットデモ |
| `demo-site/css/style.css` | **New** | 全ページ共通スタイル |
| `demo-site/js/api.js` | **New** | API通信 |
| `demo-site/js/chat.js` | **New** | チャットUI制御 |
| `demo-site/assets/salon-logo.svg` | **New** | サロンロゴ |
| `demo-site/assets/bot-avatar.svg` | **New** | ボットアイコン |
| `README.md` | **Modify** | デモサイトの説明追記 |

## 4. Implementation Priority

1. `web_chat.py` + `chat_service.py` + `rag_service.py` 修正（バックエンド）
2. `line_handler.py` リファクタ（共通化）
3. `chat.html` + `chat.js` + `api.js`（チャットデモ、最重要）
4. `index.html` + `style.css`（ランディングページ）
5. SVGアセット + OGP設定
6. `README.md` 更新

## 5. Out of Scope

- Vercelデプロイ（設計後に別途実施）
- og-image.png の実画像生成（プレースホルダーで対応）
- LINE実機スクリーンショット（後で差し替え）
- QRコード画像（プレースホルダーで対応）
