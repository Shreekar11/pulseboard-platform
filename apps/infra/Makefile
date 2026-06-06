# Static verification for the IaC. No live apply.
ENVS := aws gcp
MODULES := $(shell find modules -mindepth 2 -maxdepth 2 -type d)

.PHONY: fmt fmt-check validate tflint test verify init-lint

fmt:
	terraform fmt -recursive

fmt-check:
	terraform fmt -recursive -check

init-lint:
	tflint --init --chdir=.

validate:
	@set -e; for d in $(MODULES) $(addprefix envs/,$(ENVS)) bootstrap/aws bootstrap/gcp; do \
		echo "== validate $$d =="; \
		terraform -chdir=$$d init -backend=false -input=false >/dev/null; \
		terraform -chdir=$$d validate; \
	done

tflint:
	@set -e; for d in $(MODULES) $(addprefix envs/,$(ENVS)); do \
		echo "== tflint $$d =="; tflint --chdir=$$d; \
	done

test:
	@set -e; for d in modules/cluster/aws modules/cluster/gcp modules/database/aws modules/database/gcp; do \
		echo "== terraform test $$d =="; terraform -chdir=$$d test; \
	done

verify: fmt-check validate tflint test
	@echo "infra static checks passed"
