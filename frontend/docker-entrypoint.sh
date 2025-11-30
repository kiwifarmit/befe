#!/bin/sh
set -e

echo "Entrypoint script running..."
echo "Current directory: $(pwd)"
echo "Running as user: $(id)"

# If running as root, fix permissions and switch to appuser
if [ "$(id -u)" = "0" ]; then
    echo "Running as root, fixing permissions and switching to appuser..."
    chown -R appuser:appuser /home/appuser/app 2>/dev/null || true
    chmod -R u+w /home/appuser/app 2>/dev/null || true
    # Switch to appuser and re-exec this script
    exec su -s /bin/sh -c "exec $0 $*" appuser
fi

# Ensure node_modules directory exists
mkdir -p node_modules

# Always ensure dependencies are installed (handles volume mount scenarios)
echo "Ensuring dependencies are installed..."
npm install

echo "Verifying tailwindcss installation..."
if [ ! -d "node_modules/tailwindcss" ]; then
  echo "ERROR: tailwindcss not found after install!"
  exit 1
fi

echo "Starting dev server..."
# Start the dev server
exec npm run dev -- --host

