#!/bin/sh

echo "Creating Python 3 virtual environment" && \
    (virtualenv --python python3 --prompt "[PlatformIO Tools] " .venv && \
        echo "Done." || \
        echo "Virtual environment creation failed. Check for python3 and virtualenv in PATH.")