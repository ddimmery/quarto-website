.PHONY: help build preview clean images

.DEFAULT_GOAL := help

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
