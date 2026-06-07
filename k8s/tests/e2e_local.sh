#!/usr/bin/env bash
# Free end-to-end proof: build images, load into kind, deploy overlays/local,
# then exercise the real ingest+metrics path. Tears down on exit.
set -euo pipefail
cd "$(dirname "$0")/../.."

CLUSTER=pulseboard
cleanup() { kind delete cluster --name "$CLUSTER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "== build images =="
docker build -t pulseboard/api:local ./apps/backend
docker build -t pulseboard/frontend:local ./apps/frontend

echo "== create kind cluster =="
kind create cluster --name "$CLUSTER" --config k8s/overlays/local/kind-config.yaml

echo "== load images into kind =="
kind load docker-image pulseboard/api:local pulseboard/frontend:local --name "$CLUSTER"

echo "== install ingress-nginx (kind provider) =="
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
# Wait for the controller pod to be created before waiting for readiness
echo "   waiting for ingress-nginx controller pod to appear..."
until kubectl -n ingress-nginx get pod -l app.kubernetes.io/component=controller 2>/dev/null | grep -q controller; do sleep 2; done
kubectl wait --namespace ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=180s
# Pod "ready" doesn't guarantee the admission webhook is serving: the
# validate.nginx.ingress webhook Service can still have zero ready endpoints,
# which makes Ingress creation fail with "connection refused". Wait until the
# admission endpoints are populated before applying.
echo "   waiting for ingress-nginx admission webhook endpoints..."
until [ -n "$(kubectl -n ingress-nginx get endpoints ingress-nginx-controller-admission \
  -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null)" ]; do sleep 2; done

echo "== deploy app =="
# Even with endpoints up there's a brief admission-readiness window; retry the
# (idempotent) apply so a transient webhook hiccup doesn't fail the run.
for attempt in 1 2 3 4 5; do
  if kubectl apply -k k8s/overlays/local; then break; fi
  echo "   apply attempt $attempt failed (webhook not ready?), retrying in 5s..."
  sleep 5
  [ "$attempt" = 5 ] && { echo "apply failed after 5 attempts"; exit 1; }
done
kubectl -n pulseboard wait --for=condition=available --timeout=180s deploy/api deploy/frontend deploy/worker
kubectl -n pulseboard wait --for=condition=complete --timeout=120s job/migrate

echo "== exercise ingest + metrics via ingress (localhost:8080) =="
BASE=http://localhost:8080
curl -fsS "$BASE/healthz" >/dev/null

EVT="evt_e2e_$(date +%s)"
curl -fsS -X POST "$BASE/api/events" -H 'content-type: application/json' \
  -d "{\"event_id\":\"$EVT\",\"type\":\"signup\",\"user_id\":\"u1\",\"ts\":\"2026-01-01T10:00:00Z\"}" \
  -o /dev/null -w '%{http_code}\n' | grep -qx 202

echo "== wait for rollup freshness, then assert metrics non-empty =="
sleep 5
COUNT=$(curl -fsS "$BASE/api/metrics?type=signup&from=2026-01-01T00:00:00Z&to=2026-01-02T00:00:00Z&interval=day" \
  | jq '[.series[].count] | add // 0')
test "${COUNT:-0}" -ge 1 || { echo "expected >=1 rolled-up event, got $COUNT"; exit 1; }

echo "e2e_local.sh OK — full stack works on K8s for \$0"
