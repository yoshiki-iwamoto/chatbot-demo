# Hair Salon BLOOM - LINE チャットボット

美容室「Hair Salon BLOOM」の LINE 公式アカウント用 AI チャットボットと管理画面です。

## アーキテクチャ

```
LINE App                        Admin Browser
   │                                 │
   │ Webhook                         │ HTTPS
   ▼                                 ▼
┌──────────────────────────────────────────┐
│              Nginx (frontend)            │
│         SPA配信 + APIプロキシ             │
└──────────┬───────────────────┬───────────┘
           │ /webhook          │ /api/*
           ▼                   ▼
┌──────────────────────────────────────────┐
│           FastAPI (backend)              │
│                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ LINE    │  │ RAG     │  │ Admin   │  │
│  │ Webhook │  │ Service │  │ API     │  │
│  └────┬────┘  └────┬────┘  └────┬────┘  │
│       │            │            │        │
│  ┌────▼────┐  ┌────▼────┐  ┌───▼────┐   │
│  │ SQLite  │  │ChromaDB │  │  JWT   │   │
│  │(履歴DB) │  │(ベクトル)│  │  Auth  │   │
│  └─────────┘  └────┬────┘  └────────┘   │
│                    │                     │
│               ┌────▼────┐                │
│               │ OpenAI  │                │
│               │  API    │                │
│               └─────────┘                │
└──────────────────────────────────────────┘
```

## 機能

### LINE チャットボット
- **AI 自動応答**: FAQ データをベクトル検索 (ChromaDB) し、OpenAI API で自然文回答を生成
- **キーワード分岐**: 「予約」→ 予約ボタン、「メニュー」→ カルーセル、「アクセス」→ 地図情報
- **チャット履歴**: 全メッセージを SQLite に保存

### 管理画面
- **ダッシュボード**: 今日のメッセージ数、週間ユニークユーザー数、直近チャット
- **FAQ 管理**: CRUD 操作 + ChromaDB 自動同期
- **チャット履歴**: ユーザーごとの会話をチャット形式で表示

## 必要な環境

- Python 3.12+
- Node.js 22+
- [uv](https://docs.astral.sh/uv/) (Python パッケージ管理)
- LINE Developers アカウント
- OpenAI API キー

## LINE Developers セットアップ

1. [LINE Developers Console](https://developers.line.biz/) にログイン
2. プロバイダーを作成（または既存のものを選択）
3. **Messaging API** チャネルを作成
4. 「Messaging API設定」タブで以下を取得:
   - **チャネルシークレット** → `LINE_CHANNEL_SECRET`
   - **チャネルアクセストークン**（発行ボタンをクリック）→ `LINE_CHANNEL_ACCESS_TOKEN`
5. Webhook URL を設定（後述の ngrok URL + `/webhook`）
6. 「応答設定」で以下を変更:
   - 応答メッセージ: **オフ**
   - Webhook: **オン**

## ローカル開発

### 1. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して各種キーを設定
```

### 2. バックエンド起動

```bash
cd backend
uv sync
uv run python -m app.seed.seed_data  # 初期データ投入
uv run uvicorn app.main:app --reload  # http://localhost:8000
```

API ドキュメント: http://localhost:8000/docs

### 3. フロントエンド起動

```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

管理画面ログイン: `admin` / `admin123`

### 4. ngrok で LINE Webhook テスト

```bash
ngrok http 8000
```

表示された HTTPS URL を LINE Developers Console の Webhook URL に設定:

```
https://xxxx-xx-xx-xxx-xxx.ngrok-free.app/webhook
```

## Docker で起動

```bash
cp .env.example .env
# .env を編集

docker-compose up --build
```

- フロントエンド: http://localhost:3000
- バックエンド API: http://localhost:8000
- Webhook URL: `http://localhost:8000/webhook`（ngrok 経由で公開）

## デプロイ

### バックエンド → Render

1. [Render](https://render.com) で新規 **Web Service** を作成
2. リポジトリを接続、Root Directory: `backend`
3. Build Command: `pip install uv && uv sync`
4. Start Command: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Environment Variables に `.env` の内容を設定
6. デプロイ後、Render の URL + `/webhook` を LINE Developers に設定

### フロントエンド → Vercel

1. [Vercel](https://vercel.com) で新規プロジェクトを作成
2. リポジトリを接続、Root Directory: `frontend`
3. Framework Preset: **Vue.js**
4. Build Command: `npm run build`
5. Output Directory: `dist`

## デモサイト

ブラウザで AI チャットを体験できるデモサイトです。

### 構成

- `demo-site/index.html` — ランディングページ（機能紹介・料金プラン）
- `demo-site/chat.html` — Web チャットデモ（LINE 風 UI で AI と会話）

### ローカルで確認

バックエンドを起動した状態で、`demo-site/` 内の HTML を直接ブラウザで開くか、簡易サーバーで配信します。

```bash
# バックエンドが http://localhost:8000 で起動中
cd demo-site
python -m http.server 5500
# http://localhost:5500 でアクセス
```

API 通信はデフォルトで相対パス（`/api/web-chat`）を使用します。
ローカル開発ではプロキシまたは CORS 設定で `http://localhost:5500` を許可してください。

### デプロイ

静的サイトとして Vercel / Cloudflare Pages / Netlify にデプロイ可能です。

```bash
# Vercel の場合
cd demo-site
vercel --prod
```

## 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| `LINE_CHANNEL_SECRET` | LINE チャネルシークレット | (必須) |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE チャネルアクセストークン | (必須) |
| `OPENAI_API_KEY` | OpenAI API キー | (必須) |
| `OPENAI_MODEL` | 使用する OpenAI モデル | `gpt-4o-mini` |
| `APP_SECRET_KEY` | JWT 署名用シークレット | (必須) |
| `ADMIN_USERNAME` | 管理画面ユーザー名 | `admin` |
| `ADMIN_PASSWORD` | 管理画面パスワード | `admin123` |
| `DATABASE_URL` | SQLite DB パス | `sqlite+aiosqlite:///./data/chatbot.db` |
| `CHROMA_PERSIST_DIR` | ChromaDB 保存先 | `./data/chroma` |
| `CORS_ORIGINS` | 許可するオリジン（カンマ区切り） | `http://localhost:5173` |

## 技術スタック

**バックエンド**: Python / FastAPI / SQLAlchemy / ChromaDB / OpenAI API / LINE Bot SDK v3

**フロントエンド**: Vue 3 / Vite / TailwindCSS v4 / Pinia / Vue Router

**インフラ**: Docker / Docker Compose / Nginx
