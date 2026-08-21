#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_PATH="${REPO_ROOT}/Creative Organizer.app"
SOURCE_PATH="${APP_PATH}/Contents/Resources/Organizador.m"
BINARY_PATH="${APP_PATH}/Contents/MacOS/Organizador de Lanzamientos"
PLIST_PATH="${APP_PATH}/Contents/Info.plist"
ENGINE_PATH="${APP_PATH}/Contents/Resources/ordenar_lanzamiento.py"
BUNDLED_PYTHON="${APP_PATH}/Contents/Resources/Python3.framework/Versions/Current/bin/python3"

clang -fobjc-arc -framework Cocoa -arch arm64 -arch x86_64 "${SOURCE_PATH}" -o "${BINARY_PATH}"
chmod 755 "${BINARY_PATH}" "${ENGINE_PATH}"

plutil -lint "${PLIST_PATH}"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/creative-organizer-build-pycache" \
  "${BUNDLED_PYTHON}" -m py_compile "${ENGINE_PATH}"
codesign --force --deep --sign - "${APP_PATH}"
codesign --verify --deep --strict --verbose=2 "${APP_PATH}"

file "${BINARY_PATH}"
"${BUNDLED_PYTHON}" "${ENGINE_PATH}" --help >/dev/null
