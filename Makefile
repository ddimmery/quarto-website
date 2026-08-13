.PHONY: help build preview clean images new-post categories

.DEFAULT_GOAL := help

# Slug given as a bare argument (make new-post my-slug) or via SLUG=my-slug
SLUG ?= $(filter-out new-post,$(MAKECMDGOALS))

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

build: ## Render the site (quarto render)
	quarto render

preview: ## Live-preview the site (quarto preview)
	quarto preview

clean: ## Remove generated files (_site, .quarto)
	rm -rf _site .quarto

images: ## Standardize post images to PNG (scripts/convert_images.py)
	python scripts/convert_images.py

categories: ## List post categories with counts
	@awk ' \
		FNR == 1 { incat = 0 } \
		/^categories:/ { incat = 1; next } \
		incat && /^  - / { sub(/^  - /, ""); counts[$$0]++; next } \
		incat && !/^  / { incat = 0 } \
	END { for (c in counts) printf "%d\t%s\n", counts[c], c }' posts/*/index.qmd | \
	sort -rn | awk -F'\t' '{printf "  \033[32m%-15s\033[0m %d\n", $$2, $$1}'

new-post: ## Scaffold a new draft post: make new-post <post-slug>
	@if [ -z "$(SLUG)" ]; then \
		echo "Usage: make new-post <post-slug>"; exit 1; \
	fi
	@dir="posts/$(SLUG)"; \
	if [ -e "$$dir" ]; then \
		echo "Error: $$dir already exists"; exit 1; \
	fi; \
	mkdir -p "$$dir"; \
	{ \
		echo '---'; \
		echo 'title: "$(SLUG)"'; \
		echo 'description: ""'; \
		echo 'date: "'"$$(date +%F)"'"'; \
		echo 'categories:'; \
		echo '  - technology'; \
		echo 'image: main-image.png'; \
		echo 'draft: true'; \
		echo '---'; \
		echo ''; \
	} > "$$dir/index.qmd"; \
	echo "Created $$dir/index.qmd"

# Consume the bare slug argument so make doesn't error on it as a target.
ifeq (new-post,$(firstword $(MAKECMDGOALS)))
$(eval $(filter-out new-post,$(MAKECMDGOALS)):;@:)
endif
