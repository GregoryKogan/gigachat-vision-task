VENV := venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip3

N ?= 5
PROMPT ?= Redraw in the style of Vincent van Gogh.

DATA_DIR := data
URLS_FILE := $(DATA_DIR)/input_urls.csv
IMAGES_DIR := $(DATA_DIR)/images
CAPTIONS_FILE := $(DATA_DIR)/captions.jsonl
EDITED_DIR := $(DATA_DIR)/edited

.PHONY: all run clean clean-venv help

all: run

# --- Virtual Environment Management ---
$(VENV)/bin/activate: requirements.txt
	@echo "Setting up virtual environment..."
	python3 -m venv $(VENV) && source $(VENV)/bin/activate
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

generate: $(VENV)/bin/activate
	@echo "[1/4] Generating $(N) input URLs..."
	$(PYTHON) src/generate_input.py \
		--n $(N) \
		--output-path $(URLS_FILE)

download: generate
	@echo "[2/4] Downloading images..."
	$(PYTHON) src/download_images.py \
		--input-urls-path $(URLS_FILE) \
		--output-dir $(IMAGES_DIR)

caption: download
	@echo "[3/4] Generating captions..."
	$(PYTHON) src/generate_captions.py \
		--input-dir $(IMAGES_DIR) \
		--output-path $(CAPTIONS_FILE)

edit: download
	@echo "[4/4] Editing images with prompt: '$(PROMPT)'..."
	$(PYTHON) src/edit_images.py \
		--input-dir $(IMAGES_DIR) \
		--output-dir $(EDITED_DIR) \
		--prompt "$(PROMPT)"

run: caption edit
	@echo "Pipeline completed successfully!"
	@echo "Captions saved to: $(CAPTIONS_FILE)"
	@echo "Edited images saved to: $(EDITED_DIR)"

clean:
	@echo "Cleaning data and logs..."
	rm -rf $(DATA_DIR)
	rm -rf logs

clean-venv:
	@echo "Removing virtual environment..."
	rm -rf $(VENV)

help:
	@echo "Usage:"
	@echo "  make run                       # Run pipeline with defaults (N=5)"
	@echo "  make run N=10                  # Run for 10 images"
	@echo "  make run PROMPT='Your prompt'  # Run with custom edit prompt"
	@echo "  make clean                     # Remove data folder"
	@echo "  make clean-venv                # Remove virtual environment"
