from __future__ import annotations

import json
import os
import random
import sqlite3
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from benchmarks.frameworks.shared import (
    DB_PATH, LARGE_PAYLOAD, SAMPLE_TEXT_PATH,
    UserProfileDataclass, jinja_env
)

# Custom Django Middleware for dynamic stacking
class DummyDjangoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        # minor work
        request.META["django_layer"] = True
        return self.get_response(request)

# Inline Django Configuration
if not settings.configured:
    middleware_stack = []
    layers_count = int(os.environ.get("MIDDLEWARE_LAYERS", "0"))
    for i in range(layers_count):
        middleware_stack.append("benchmarks.frameworks.django.main.DummyDjangoMiddleware")
    
    settings.configure(
        DEBUG=False,
        SECRET_KEY="django-insecure-benchmark-secret-key-that-is-very-long",
        ROOT_URLCONF="benchmarks.frameworks.django.main",
        MIDDLEWARE=middleware_stack,
        ALLOWED_HOSTS=["*"],
        APPEND_SLASH=False,
    )

# Setup Django application context
import django
django.setup()

def get_sync_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# Views
def health(request):
    return HttpResponse("ok", content_type="text/plain")

def plaintext(request):
    return HttpResponse("Hello, World!", content_type="text/plain")

def json_endpoint(request):
    return JsonResponse({"message": "Hello, World!"})

def json_large(request):
    return JsonResponse(LARGE_PAYLOAD)

def db_single(request):
    with get_sync_db() as db:
        row_id = random.randint(1, 10000)
        cursor = db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,))
        row = cursor.fetchone()
        return JsonResponse({"id": row["id"], "randomNumber": row["randomNumber"]})

def db_queries(request):
    queries = request.GET.get("queries", "1")
    try:
        q_val = int(queries)
    except ValueError:
        q_val = 1
    q_val = max(1, min(500, q_val))

    results = []
    with get_sync_db() as db:
        for _ in range(q_val):
            row_id = random.randint(1, 10000)
            cursor = db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,))
            row = cursor.fetchone()
            results.append({"id": row["id"], "randomNumber": row["randomNumber"]})
    return JsonResponse(results, safe=False)

def db_updates(request):
    queries = request.GET.get("queries", "1")
    try:
        q_val = int(queries)
    except ValueError:
        q_val = 1
    q_val = max(1, min(500, q_val))

    results = []
    with get_sync_db() as db:
        for _ in range(q_val):
            row_id = random.randint(1, 10000)
            new_num = random.randint(1, 10000)
            cursor = db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,))
            row = cursor.fetchone()
            db.execute("UPDATE world SET randomNumber = ? WHERE id = ?", (new_num, row_id))
            results.append({"id": row_id, "randomNumber": new_num})
        db.commit()
    return JsonResponse(results, safe=False)

def fortunes(request):
    with get_sync_db() as db:
        cursor = db.execute("SELECT id, message FROM fortune")
        rows = cursor.fetchall()
        fortunes_list = [{"id": r["id"], "message": r["message"]} for r in rows]
    
    fortunes_list.append({"id": 0, "message": "Additional fortune added at runtime."})
    fortunes_list.sort(key=lambda x: x["message"])
    
    template = jinja_env.get_template("fortunes.html")
    rendered = template.render(fortunes=fortunes_list)
    return HttpResponse(rendered, content_type="text/html")

CACHE_STORE = {i: random.randint(1, 10000) for i in range(1, 10001)}

def cached_test(request):
    queries = request.GET.get("queries", "1")
    try:
        q_val = int(queries)
    except ValueError:
        q_val = 1
    q_val = max(1, min(500, q_val))
    
    results = []
    for _ in range(q_val):
        row_id = random.randint(1, 10000)
        val = CACHE_STORE.get(row_id)
        if val is None:
            with get_sync_db() as db:
                cursor = db.execute("SELECT randomNumber FROM world WHERE id = ?", (row_id,))
                row = cursor.fetchone()
                val = row["randomNumber"]
                CACHE_STORE[row_id] = val
        results.append({"id": row_id, "randomNumber": val})
    return JsonResponse(results, safe=False)

@csrf_exempt
def validation_dataclass(request):
    if request.method == "POST":
        data = json.loads(request.body)
        payload = UserProfileDataclass.from_dict(data)
        return JsonResponse({"ok": True, "username": payload.username})
    return HttpResponse(status=405)

def route_static(request):
    return JsonResponse({"route": "static"})

def route_params(request, user_id, order_id):
    return JsonResponse({"user_id": int(user_id), "order_id": int(order_id)})

def di_chain(request):
    return JsonResponse({"value": (21 + 11) * 2})

@csrf_exempt
def body_multipart(request):
    if request.method == "POST":
        upload_file = request.FILES.get("file")
        if upload_file:
            content = upload_file.read()
            return JsonResponse({"filename": upload_file.name, "size": len(content)})
        return JsonResponse({"filename": "unknown", "size": 0})
    return HttpResponse(status=405)

def response_stream(request):
    # Django streaming response
    from django.http import StreamingHttpResponse
    import time
    def chunk_stream():
        for idx in range(32):
            yield f"chunk-{idx:03d}:{'x'*1000}\n"
            time.sleep(0.001)
    return StreamingHttpResponse(chunk_stream(), content_type="application/octet-stream")

# Define URL configurations
urlpatterns = [
    path("health", health),
    path("plaintext", plaintext),
    path("json", json_endpoint),
    path("json/large", json_large),
    path("db", db_single),
    path("queries", db_queries),
    path("updates", db_updates),
    path("fortunes", fortunes),
    path("cached", cached_test),
    path("validation/dataclass", validation_dataclass),
    path("route/static", route_static),
    path("route/params/<int:user_id>/orders/<int:order_id>", route_params),
    path("di", di_chain),
    path("body/multipart", body_multipart),
    path("response/stream", response_stream),
]

# Filler routes to benchmark large route tables
for slot in range(500):
    exec(f"""
def filler_{slot}(request):
    return JsonResponse({{"slot": {slot}}})
urlpatterns.append(path("route/filler/r{slot}", filler_{slot}))
""")

app = get_asgi_application()
