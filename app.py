def app(environ, start_response):
    path = environ.get("PATH_INFO", "/") or "/"

    if path == "/favicon.ico":
        start_response("204 No Content", [("Content-Type", "text/plain")])
        return [b""]

    if path == "/health":
        body = b'{"status":"ok"}'
        start_response("200 OK", [("Content-Type", "application/json")])
        return [body]

    body = b'{"name":"Urdu Bible API","status":"starting"}'
    start_response("200 OK", [("Content-Type", "application/json")])
    return [body]
