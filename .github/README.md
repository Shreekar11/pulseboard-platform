# PulseBoard CI/CD (Phase 5)

Two GitHub Actions workflows. **Cloud-specific detail lives behind a single switch.**

## Workflows
- **`ci.yml`** — validation. Runs on PRs to `main` and pushes to any branch:
  `actionlint`, backend (`ruff` + `pytest` via `uv`, testcontainers), frontend
  (`pnpm lint` + `build`), `infra-static` (`make -C apps/infra verify`),
  `k8s-render` (`render.sh`), `docker-build` (both images, no push), and `e2e-kind`
  (`e2e_local.sh`, PRs to `main` only).
- **`deploy.yml`** — delivery. Runs on push to `main` and `workflow_dispatch`:
  `terraform apply` → build/push images → create `pulseboard-db` secret →
  `kustomize set image` + `kubectl apply -k` → rollout → ingress health check →
  optional AI deploy summary.

## The single switch
`vars.CLOUD_PROVIDER` (`aws` or `gcp`) selects the target cloud. Retarget by changing
that one repo variable. For a one-off run, use **Run workflow → `cloud_provider`** to
override. Resolution: `inputs.cloud_provider || vars.CLOUD_PROVIDER`.

The only cloud-specific code is the `cloud-auth` composite action (OIDC + CLI) plus two
registry-login steps; everything else (Terraform module wiring, Kustomize base/overlays,
deploy steps) is identical across clouds. Adding a third cloud = add a branch to
`cloud-auth` + the existing additive `envs/<cloud>` and `overlays/<cloud>`.

## Required repo configuration (set up in Phase 6)
Authentication is keyless OIDC — no long-lived cloud keys are stored.

| Kind | Name | Purpose |
|------|------|---------|
| variable | `CLOUD_PROVIDER` | the single switch (`aws`\|`gcp`) |
| variable | `AWS_REGION` | AWS region |
| variable | `GCP_REGION`, `GCP_PROJECT_ID` | GCP coordinates |
| secret | `AWS_ROLE_ARN` | IAM role assumed via GitHub OIDC |
| secret | `GCP_WIF_PROVIDER`, `GCP_SERVICE_ACCOUNT` | GCP Workload Identity Federation |
| secret | `ANTHROPIC_API_KEY` | optional — enables the AI deploy-summary step |

Cloud-side trust (AWS IAM OIDC provider + role; GCP WIF pool + SA bindings) is created
during the Phase-6 bootstrap.

## Validate for free
`actionlint` validates every workflow (a CI job). The deploy *logic* is functionally
proven against a local `kind` cluster by `k8s/tests/e2e_local.sh`. Live `apply` to AWS/GCP
is Phase 6. Until `CLOUD_PROVIDER` and the OIDC secrets exist, `deploy.yml` fails fast on
the "resolve provider" step rather than half-deploying.
