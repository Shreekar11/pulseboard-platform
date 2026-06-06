# PulseBoard K8s manifests (Kustomize)

`base/` is cloud-agnostic. `overlays/{aws,gcp,local}/` patch only the cloud-specific delta
(ingress class/annotations, StorageClass, image registry, ServiceAccount, and — local only —
an in-cluster Postgres pod + dev secret).

## Single switch
    kubectl apply -k k8s/overlays/$CLOUD_PROVIDER   # aws | gcp | local

## The DB secret seam
`base` references Secret `pulseboard-db` (key `DATABASE_URL`) but does not create it:
- **local** overlay ships a dev secret pointing at the in-cluster Postgres pod.
- **aws/gcp**: CI creates the secret from the Terraform `db_dsn` output before `apply`.

## Validate (free)
    bash k8s/tests/render.sh     # render + schema + delta assertions (all overlays)
    bash k8s/tests/e2e_local.sh  # kind end-to-end (build, deploy, ingest, assert rollup)

## Add a 3rd cloud
Add `overlays/<cloud>/` patching the same four deltas. Base is untouched.
