#!/bin/bash

echo -e "Running Pylint on Temporal App..."
find . -name "*.py" | xargs pylint --disable=missing-module-docstring,missing-class-docstring
