#!/bin/bash
# Server initial setup script for GCE Ubuntu/Debian
# Run once on new server: bash setup-server.sh

set -e

echo "=== Installing Docker ==="
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker $USER

echo "=== Installing Git ==="
sudo apt-get install -y git

echo "=== Cloning AIStarlight ==="
cd ~
git clone https://github.com/tonypk/aistarlight.git
cd aistarlight

echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Log out and back in (for docker group)"
echo "  2. cp .env.example .env && vim .env  (set secrets)"
echo "  3. docker compose -f docker-compose.prod.yml up -d"
echo "  4. docker compose -f docker-compose.prod.yml exec backend alembic upgrade head"
