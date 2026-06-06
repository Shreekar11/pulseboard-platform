# envs/local

There is **no Terraform** for local. The local target is a `kind` cluster created by the
end-to-end harness (`k8s/tests/e2e_local.sh`) and the `k8s/overlays/local` Kustomize overlay.
This keeps local validation on the same K8s/Kustomize path as the cloud targets while
costing nothing. See `k8s/README.md`.
