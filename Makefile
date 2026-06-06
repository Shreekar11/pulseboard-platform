.PHONY: verify infra-verify k8s-verify e2e-local

verify: infra-verify k8s-verify
	@echo "ALL Phase-4 static gates passed"

infra-verify:
	$(MAKE) -C apps/infra verify

k8s-verify:
	bash k8s/tests/render.sh

e2e-local:
	bash k8s/tests/e2e_local.sh
