# BeyondConnect Chatbot (Django + Cloudflare Workers AI)

A ChatGPT-style shopping assistant for https://beyondconnect.store, powered by Cloudflare Workers AI.

## Features
- Clean chat UI (light/dark), suggestion chips, typing indicator, "New chat", conversation memory
- Knows your products: it searches your catalog for each question and gives Gemini only the relevant items,
  so answers use real names, prices and links (it is told never to invent any)
- Free-quota protection: a daily counter (`DAILY_LIMIT`) plus a per-visitor rate limit
- Conversations saved in the database and visible in `/admin`
- Embeddable on your store as an iframe or a floating chat bubble

## 1. Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
```
Open `.env` and fill in `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` (see the Cloudflare section below).

## 2. Database + catalog
```bash
python manage.py makemigrations chat
python manage.py migrate
python manage.py createsuperuser
python manage.py sync_products          # pulls products from beyondconnect.store
# python manage.py sync_products --demo # offline sample products instead
```
Check `/admin` > Products. Fix any wrong price/category by hand, or add products manually.
Re-run `sync_products` whenever your catalog changes (or schedule it with cron).

## 3. Run
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000/

## 4. Put it on your store
Floating bubble (add before `</body>` in your store's base template):
```html
<script src="https://YOUR-CHATBOT-DOMAIN/static/chat/widget.js" data-src="https://YOUR-CHATBOT-DOMAIN/"></script>
```
Or a plain link/iframe to `https://YOUR-CHATBOT-DOMAIN/`.

## 5. Deploy
Any Python host works (Render, Railway, PythonAnywhere, a VPS):
```bash
python manage.py collectstatic --noinput
gunicorn beyondconnect_bot.wsgi
```
Set in production: `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=your-domain`,
`CSRF_TRUSTED_ORIGINS=https://your-domain`.

## Cloudflare Workers AI setup
1. Sign in at https://dash.cloudflare.com and copy your **Account ID** (right sidebar of the dashboard home).
2. Go to My Profile > API Tokens > Create Token, use the **Workers AI** template, and copy the token.
3. Put both in `.env`. Pick a model with `CLOUDFLARE_MODEL` (see the Workers AI model catalog).

Free plan: 10,000 "neurons" per day, resetting at 00:00 UTC. Above that, requests fail on the Free plan.
To never run out, upgrade to the Workers Paid plan: you pay about $0.011 per 1,000 extra neurons.
Smaller models (like the 8B default) fit many more chats into the free allowance than 70B models.

## Project layout
```
manage.py
requirements.txt
.env.example
beyondconnect_bot/     settings, urls, wsgi/asgi
chat/
  models.py            Product, Conversation, Message, DailyUsage
  catalog.py           finds products relevant to the question
  llm.py               system prompt + Cloudflare AI call
  views.py             chat page + JSON API
  management/commands/sync_products.py
  templates/chat/index.html
  static/chat/         style.css, app.js, widget.js
```

## Customising the bot
Edit `build_system_prompt()` in `chat/llm.py` to change tone, add delivery areas, warranty, payment methods,
WhatsApp number, etc. The bot only states store facts that you put there.
"# beyondconnect_chatbot" 
