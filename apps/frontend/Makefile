SPEC_SRC := ../backend/openapi/openapi.json
SPEC_DEST := openapi/openapi.json
GENERATED_DIR := lib/generated

.PHONY: sync-spec gen generate

sync-spec:
	mkdir -p openapi
	cp $(SPEC_SRC) $(SPEC_DEST)

gen:
	pnpm exec openapi --input $(SPEC_DEST) \
		--output $(GENERATED_DIR) \
		--exportServices false \
		--exportCore false \
		--useUnionTypes

generate: sync-spec gen
