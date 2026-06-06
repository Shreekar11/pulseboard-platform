#!/usr/bin/env bash
# Renders every overlay, schema-validates with kubeconform, and asserts deltas.
set -euo pipefail
cd "$(dirname "$0")/../.."

render() { kubectl kustomize "k8s/overlays/$1"; }

echo "== schema-validate base via local overlay =="
render local | kubeconform -strict -summary -ignore-missing-schemas

echo "== assert: ConfigMap carries Redis buffer URL =="
render local | yq 'select(.kind=="ConfigMap") | .data.REDIS_BUFFER_URL' | grep -q 'redis://redis:6379/0'

echo "== assert: all base workloads present =="
out="$(render local)"
for kind_name in "StatefulSet redis" "Deployment api" "Deployment worker" "Deployment frontend" "Job migrate" "Ingress pulseboard"; do
  k="${kind_name% *}"; n="${kind_name#* }"
  echo "$out" | yq "select(.kind==\"$k\" and .metadata.name==\"$n\") | .metadata.name" | grep -qx "$n" \
    || { echo "MISSING $k/$n"; exit 1; }
done

echo "== assert: api reads DATABASE_URL from secret pulseboard-db =="
echo "$out" | yq 'select(.kind=="Deployment" and .metadata.name=="api") | .spec.template.spec.containers[0].env[] | select(.name=="DATABASE_URL") | .valueFrom.secretKeyRef.name' | grep -qx 'pulseboard-db'

echo "== assert: aws overlay deltas =="
a="$(render aws)"
echo "$a" | yq 'select(.kind=="Ingress") | .spec.ingressClassName' | grep -qx 'alb'
echo "$a" | yq 'select(.kind=="StatefulSet" and .metadata.name=="redis") | .spec.volumeClaimTemplates[0].spec.storageClassName' | grep -qx 'gp3'
echo "$a" | yq 'select(.kind=="Deployment" and .metadata.name=="api") | .spec.template.spec.containers[0].image' | grep -q 'REGISTRY/pulseboard/api'

echo "== assert: gcp overlay deltas =="
g="$(render gcp)"
echo "$g" | yq 'select(.kind=="Ingress") | .spec.ingressClassName' | grep -qx 'gce'
echo "$g" | yq 'select(.kind=="StatefulSet" and .metadata.name=="redis") | .spec.volumeClaimTemplates[0].spec.storageClassName' | grep -qx 'pd-balanced'

echo "== assert: local overlay ships postgres + db secret =="
l="$(render local)"
echo "$l" | yq 'select(.kind=="StatefulSet" and .metadata.name=="postgres") | .metadata.name' | grep -qx 'postgres'
echo "$l" | yq 'select(.kind=="Secret" and .metadata.name=="pulseboard-db") | .metadata.name' | grep -qx 'pulseboard-db'

echo "render.sh OK"
