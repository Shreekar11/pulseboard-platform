# PulseBoard — Cloud-Agnostic IaC

Terraform provisions the four cloud-specific primitives (cluster, managed Postgres,
networking, registry); the K8s app layer ships separately via Kustomize (`/k8s`).

## Layout
- `modules/<type>/<cloud>/` — per-provider impls honoring one contract (see Phase-4-IaC spec §5).
- `envs/<cloud>/` — thin roots: provider + backend + module wiring + the `cluster_auth`/`registry_url`/`db_dsn` outputs.
- `bootstrap/<cloud>/` — one-time state-store creation (run before the first `init`).

## Single switch
    CLOUD=aws   # or gcp
    terraform -chdir=envs/$CLOUD init
    terraform -chdir=envs/$CLOUD apply -var-file=$CLOUD.tfvars   # Phase 6 (live)

## Add a 3rd cloud (e.g. DigitalOcean)
Create `modules/{network,cluster,database,registry}/do/` honoring the same contract,
`envs/do/`, and `k8s/overlays/do/`. Zero edits to AWS/GCP. That additivity is the point.

## Static verification (this phase — no live apply)
    make verify        # fmt-check + validate + tflint + terraform test (all modules/envs)
    make -C .. e2e-local   # kind end-to-end (from repo root: make e2e-local)

## One-time bootstrap (before first cloud apply, Phase 6)
    terraform -chdir=bootstrap/aws apply
    terraform -chdir=bootstrap/gcp apply -var project_id=<id>
