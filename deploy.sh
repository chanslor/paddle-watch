#!/bin/bash
cd /chanslor/mdc/YOUTUBE/paddle-watch
echo "Current directory: $(pwd)"
echo "Files:"
ls -la
echo ""
echo "Deploying to Fly.io..."
fly deploy --local-only
