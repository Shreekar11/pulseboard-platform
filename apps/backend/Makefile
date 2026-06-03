.PHONY: gen gen-check

# Codegen flags shared by `gen` and `gen-check`. Keep these in sync so the
# diff in `gen-check` is meaningful (deterministic output, no timestamp).
CODEGEN_FLAGS = \
	--input openapi/openapi.json \
	--input-file-type openapi \
	--output-model-type pydantic_v2.BaseModel \
	--target-python-version 3.12 \
	--use-annotated \
	--field-constraints \
	--use-default \
	--allow-population-by-field-name \
	--disable-timestamp \
	--custom-file-header-path openapi/generated_header.txt

gen:
	uv run datamodel-codegen $(CODEGEN_FLAGS) --output app/models/generated.py

gen-check:
	uv run datamodel-codegen $(CODEGEN_FLAGS) --output /tmp/generated_check.py
	diff app/models/generated.py /tmp/generated_check.py
