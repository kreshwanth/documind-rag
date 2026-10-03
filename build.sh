#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Building DocuMind Frontend ---"
cd frontend
rm -rf node_modules
rm -f package-lock.json
npm install --include=optional
npm run build
cd ..

echo "--- Installing Backend Dependencies ---"
cd backend
pip install -r requirements.txt
cd ..

echo "--- DocuMind Build Complete ---"
