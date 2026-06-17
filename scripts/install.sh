#!/usr/bin/env bash
set -e

BASE_DIR="/opt/friday"
BRANCH="friday-agent/poc"

if [ "$EUID" -ne 0 ]; then
  echo "Dieses Installationsskript empfiehlt Root-Rechte für systemd-Installation. Starte mit sudo." >&2
fi

echo "Erstelle Verzeichnis $BASE_DIR"
mkdir -p $BASE_DIR

echo "Kopiere Dateien (lokal aus Repo)..."
# Für PoC: Annahme: Skript ausgeführt im Repo-Checkout
cp -r . $BASE_DIR

echo "Erstelle Python venv und installiere Abhängigkeiten"
python3 -m venv $BASE_DIR/venv
$BASE_DIR/venv/bin/pip install --upgrade pip
$BASE_DIR/venv/bin/pip install psutil pyyaml

echo "Installiere systemd service (falls vorhanden)"
SERVICE_PATH="/etc/systemd/system/friday-agent.service"
cp $BASE_DIR/systemd/friday-agent.service $SERVICE_PATH
systemctl daemon-reload
systemctl enable friday-agent
systemctl start friday-agent

echo "Installation abgeschlossen. Service gestartet (falls systemd vorhanden)."
