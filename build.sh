#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Building DocuMind Frontend ---"
cd frontend
npm install
npm run build
cd ..

echo "--- Installing Backend Dependencies ---"
cd backend
pip install -r requirements.txt
cd ..

echo "--- DocuMind Build Complete ---"
