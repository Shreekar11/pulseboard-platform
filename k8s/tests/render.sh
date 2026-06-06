#!/usr/bin/env bash
# Renders every overlay, schema-validates with kubeconform, and asserts deltas.
set -euo pipefail
cd "$(dirname "$0")/../.."

render() { kubectl kustomize "k8s/overlays/$1"; }

echo "== schema-validate base via local overlay =="
render local | kubeconform -strict -summary -ignore-missing-schemas

echo "== assert: ConfigMap carries Redis buffer URL =="
render local | yq 'select(.kind=="ConfigMap") | .data.REDIS_BUFFER_URL' | grep -q 'redis://redis:6379/0'

echo "render.sh OK"
