#!/bin/bash
# Install DevBoard Hermes plugin
set -euo pipefail

HERMES_PLUGINS="${HERMES_HOME:-$HOME/.hermes}/plugins"
PLUGIN_NAME="rapidwebs-devboard"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing DevBoard Hermes plugin..."
mkdir -p "$HERMES_PLUGINS/$PLUGIN_NAME"
cp -r "$SOURCE_DIR/$PLUGIN_NAME/"* "$HERMES_PLUGINS/$PLUGIN_NAME/"
echo "Installed to $HERMES_PLUGINS/$PLUGIN_NAME/"
echo ""
echo "Done. Restart Hermes or start a new session to load the plugin."
