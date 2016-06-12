#!/bin/bash
cd "$(dirname "$0")"
rm -rf build dist
python setup.py bdist_wheel --universal sdist
