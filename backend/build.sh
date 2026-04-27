#!/usr/bin/env bash
set -e

echo "==> Installing Node deps and building React..."
cd frontend
npm install
npm run build
cd ..

echo "==> Copying React build into Flask static folder..."
rm -rf backend/static
cp -r frontend/dist backend/static

echo "==> Installing Python deps..."
cd backend
pip install -r requirements.txt

echo "==> Build complete."
