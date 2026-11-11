import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .llm import ChatError, generate_reply
from .models import Conversation, DailyUsage, Message

log = logging.getLogger(__name__)


def _client_ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    return fwd.split(",")[0].strip() if fwd else request.META.get("REMOTE_ADDR", "unknown")


@xframe_options_exempt  # lets you embed the chat in your store with an <iframe>
def index(request):
    return render(request, "chat/index.html")


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt  # public, anonymous endpoint; protected by rate limits instead
@require_POST
def api_chat(request):
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    text = str(data.get("message", "")).strip()
    if not text:
        return JsonResponse({"error": "Please type a message."}, status=400)
    if len(text) > settings.MAX_MESSAGE_CHARS:
        return JsonResponse({"error": f"Message too long (max {settings.MAX_MESSAGE_CHARS} characters)."}, status=400)

    # per-visitor rate limit
    key = f"rl:{_client_ip(request)}"
    cache.add(key, 0, 60)
    if cache.incr(key) > settings.IP_RATE_LIMIT_PER_MIN:
        return JsonResponse({"error": "You're sending messages too fast. Please wait a moment."}, status=429)

    # find or create conversation
    conv = None
    cid = data.get("conversation_id")
    if cid:
        try:
            conv = Conversation.objects.filter(pk=cid).first()
        except (ValueError, TypeError):
            conv = None
    if conv is None:
        conv = Conversation.objects.create()

    # daily free-quota guard
    if not DailyUsage.take(settings.DAILY_LIMIT):
        return JsonResponse(
            {"error": "Our assistant has reached its daily limit. Please try again tomorrow or visit our contact page."},
            status=429,
        )

    recent = list(conv.messages.order_by("-created_at", "-id")[: settings.HISTORY_TURNS])[::-1]
    history = [(m.role, m.content) for m in recent]
    while history and history[0][0] != "user":  # Gemini expects the first turn to be from the user
        history.pop(0)

    try:
        reply = generate_reply(history, text)
    except ChatError as e:
        return JsonResponse({"error": e.user_message, "conversation_id": str(conv.id)}, status=e.status)

    Message.objects.create(conversation=conv, role="user", content=text)
    Message.objects.create(conversation=conv, role="model", content=reply)
    return JsonResponse({"reply": reply, "conversation_id": str(conv.id)})


@require_GET
def api_history(request, cid):
    conv = Conversation.objects.filter(pk=cid).first()
    if not conv:
        return JsonResponse({"messages": []})
    msgs = [{"role": m.role, "content": m.content} for m in conv.messages.all()]
    return JsonResponse({"messages": msgs})
