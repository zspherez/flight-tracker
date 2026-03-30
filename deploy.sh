#!/bin/bash
set -e

echo "=== Preparing deployment ==="

# Copy fli library into backend build context
echo "Copying fli library..."
rm -rf backend/fli
cp -r ../fli backend/fli
# Remove unnecessary files from the copy
rm -rf backend/fli/.git backend/fli/tests backend/fli/docs backend/fli/node_modules

echo "=== Ready to deploy ==="
echo ""
echo "To deploy to your GCP VM:"
echo "  1. Push this folder to the VM:"
echo "     gcloud compute scp --recurse ~/misc/flight_tracker <instance>:~/flight_tracker --zone <zone>"
echo ""
echo "  2. SSH into the VM:"
echo "     gcloud compute ssh <instance> --zone <zone>"
echo ""
echo "  3. On the VM, run:"
echo "     cd ~/flight_tracker"
echo "     docker compose up -d --build"
echo ""
echo "  4. Open http://<vm-external-ip> in your browser"
