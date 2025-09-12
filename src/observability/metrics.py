from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['route', 'method', 'code'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['route'])

def prometheus_wsgi_app(environ, start_response):
    data = generate_latest()
    start_response('200 OK', [('Content-Type', CONTENT_TYPE_LATEST)])
    return [data]
