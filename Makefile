.PHONY: build preview clean images

build:
	quarto render

preview:
	quarto preview

clean:
	rm -rf _site .quarto

images:
	python scripts/convert_images.py
