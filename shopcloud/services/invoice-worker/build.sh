#!/usr/bin/env bash
# Build a Lambda zip for the invoice worker.
#
# Lambda zip layout: dependencies and source must be at the zip root, like:
#   handler.py
#   reportlab/...
#   boto3/...   (Lambda already has boto3 but we pin our version)
#
# We don't ship `src/` as a folder because that complicates the import path -
# we copy handler.py and pdf.py to the root.
#
# Usage: ./build.sh         -> writes dist/invoice-worker.zip
#        ./build.sh /tmp/x  -> writes /tmp/x/invoice-worker.zip
set -euo pipefail

cd "$(dirname "$0")"

OUT_DIR="${1:-dist}"
mkdir -p "$OUT_DIR"
ZIP_PATH="$OUT_DIR/invoice-worker.zip"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

echo "==> Installing dependencies into $WORK_DIR"
pip install --quiet --target "$WORK_DIR" -r requirements.txt

echo "==> Copying source"
cp src/handler.py "$WORK_DIR/handler.py"
cp src/pdf.py "$WORK_DIR/pdf.py"

# Patch the import: handler.py uses `from src.pdf import` but in Lambda we
# flatten to root, so rewrite to `from pdf import`.
# (Portable sed — macOS BSD sed needs `sed -i ''`; redirect works everywhere.)
sed 's/from src\.pdf import/from pdf import/' "$WORK_DIR/handler.py" >"$WORK_DIR/handler.py.tmp"
mv "$WORK_DIR/handler.py.tmp" "$WORK_DIR/handler.py"

echo "==> Zipping to $ZIP_PATH"
rm -f "$ZIP_PATH"
( cd "$WORK_DIR" && zip -qr "$OLDPWD/$ZIP_PATH" . )

echo ""
echo "Lambda handler:        handler.lambda_handler"
echo "Zip:                   $ZIP_PATH ($(du -h "$ZIP_PATH" | cut -f1))"
