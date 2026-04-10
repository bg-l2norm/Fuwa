#!/bin/bash
echo "Test 1: venv is a file"
rm -rf venv
touch venv
./fuwa.sh install

echo "Test 2: venv is empty directory"
rm -rf venv
mkdir venv
# don't run as it will actually run the app! instead do update to see if it fixes it.
./fuwa.sh update

echo "Test 3: requirements.txt is missing"
rm -rf venv
mv requirements.txt req.bak
./fuwa.sh install
mv req.bak requirements.txt
