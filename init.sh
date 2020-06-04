#!/bin/sh

echo "Creating Python 3 virtual environment" && \
    virtualenv -p python3 .venv && \
    echo "Done." || echo "Virtual environment creation failed. Check for python3 and virtualenv in PATH."