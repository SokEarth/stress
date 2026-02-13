from flask import Flask, render_template, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import random

app = Flask(__name__)

# -------------------
# Prometheus Metrics
# -------------------

REQUEST_COUNT = Counter(
  "http_requests_total",
  "Total HTTP Requests",
  ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
  "http_request_duration_seconds",
  "HTTP Request Latency",
  ["endpoint"]
)

IN_PROGRESS = Gauge(
  "http_requests_in_progress",
  "Number of in-progress HTTP requests"
)

# -------------------
# Request Hooks
# -------------------
@app.before_request
def before_request():
  request.start_time = time.time()
  IN_PROGRESS.inc()

@app.after_request
def after_request(response):
  resp_time = time.time() - request.start_time

  REQUEST_COUNT.labels(
    method=request.method,
    endpoint=request.path,
    http_status=response.status_code
  ).inc()

  REQUEST_LATENCY.labels(
    endpoint=request.path
  ).observe(resp_time)

  IN_PROGRESS.dec()

  return response

# -------------------
# Routes
# -------------------

@app.route("/")
def home():
  return render_template("home.html")

@app.route("/route1")
def route1():
  return render_template("route1.html")

@app.route("/route2")
def route2():
  return render_template("route2.html")

# Simulates latency (default 2 seconds, override with ?delay=5)
@app.route("/slow")
def slow():
  delay = float(request.args.get("delay", 2))
  time.sleep(delay)
  return render_template("slow.html", delay=delay)

# Simulates errors (50% failure by default, override with ?rate=0.8)
# Simulates errors (50% failure by default, override with ?rate=0.8)
@app.route("/error")
def error():
  failure_rate = float(request.args.get("rate", 0.5))
  if random.random() < failure_rate:
    return render_template("error.html"), 500
  return render_template("error.html")

# Prometheus endpoint
@app.route("/metrics")
def metrics():
  return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8080)