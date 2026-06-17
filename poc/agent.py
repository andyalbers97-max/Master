"""
friday PoC Agent (minimal)
- Überwacht einfache Systemmetriken
- Bewertet Events mit heuristischem ThreatScore
- Interagiert mit dem Benutzer vor Routine-Aktionen
- Führt autonome Maßnahmen bei hohen Scores aus (konfigurierbar)
- Bietet Schnittstellen zu Bitwarden (CLI) und KeePass (pykeepass)
- Einfache lokale Persistenz für Events und Labels (sqlite)

Dieses Skript ist ein Proof-of-Concept und sollte nicht ungeprüft mit Admin-Rechten in Produktionssystemen ausgeführt werden.
"""
import os
import sys
import time
import yaml
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import psutil
except Exception:
    print("Bitte installiere psutil: pip install psutil")
    sys.exit(1)

# Optional ML: sklearn SGDClassifier for partial_fit
try:
    from sklearn.linear_model import SGDClassifier
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / 'config' / 'example.yaml'
DB_PATH = BASE_DIR / 'poc' / 'friday.db'
QUARANTINE_DIR = BASE_DIR / 'poc' / 'quarantine'

os.makedirs(QUARANTINE_DIR, exist_ok=True)

# Simple event store + label store
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    type TEXT,
    payload TEXT,
    score REAL,
    acted INTEGER DEFAULT 0
)")
cur.execute('''CREATE TABLE IF NOT EXISTS labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    label INTEGER,
    ts TEXT
)''')
conn.commit()

# Load config
with open(CONFIG_PATH) as f:
    CONFIG = yaml.safe_load(f)

THRESH_AUTONOMOUS = CONFIG.get('thresholds', {}).get('autonomous', 0.85)
THRESH_SUGGEST = CONFIG.get('thresholds', {}).get('suggest', 0.5)

# Simple incremental model wrapper
class SimpleModel:
    def __init__(self):
        self.model = None
        if SKLEARN_AVAILABLE:
            # Binary classifier (0 = benign, 1 = malicious)
            self.model = SGDClassifier(loss='log')
            # We'll lazily call partial_fit with classes
            self.initialized = False
        else:
            self.weights = None

    def predict_proba(self, features):
        if SKLEARN_AVAILABLE and self.initialized:
            p = self.model.predict_proba([features])[0][1]
            return p
        # fallback: heuristic
        s = 0.0
        s += min(1.0, features[0] / 100.0) * 0.4  # cpu
        s += min(1.0, features[1] / 1000000.0) * 0.4  # io
        s += (1.0 if features[2] else 0.0) * 0.2  # network suspicious
        return s

    def update(self, X, y):
        if SKLEARN_AVAILABLE:
            if not self.initialized:
                self.model.partial_fit(X, y, classes=[0,1])
                self.initialized = True
            else:
                self.model.partial_fit(X, y)
        else:
            # no-op for PoC
            pass

MODEL = SimpleModel()

# Helpers: evaluate event
def evaluate_event(evt):
    # evt: dict with cpu, io_bytes, suspicious_net boolean
    feat = [evt.get('cpu',0), evt.get('io_bytes',0), 1 if evt.get('susp_net') else 0]
    score = MODEL.predict_proba(feat)
    return float(score), feat

# Interaction helpers
def prompt_user(prompt, timeout=None, default=None):
    # For PoC: simple blocking input
    print('\n[friday] ' + prompt)
    try:
        res = input('Antwort (ja/nein/später): ').strip().lower()
    except Exception:
        return default
    return res

# Bitwarden integration (requires bw CLI and logged-in session)
def bw_list(session=None):
    try:
        cmd = ['bw', 'list', 'items']
        if session:
            cmd = ['bw', '--session', session, 'list', 'items']
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print('Bitwarden CLI Fehler:', r.stderr)
            return []
        return json.loads(r.stdout)
    except FileNotFoundError:
        print('Bitwarden CLI (bw) nicht gefunden')
        return []

def bw_show_item(item_id, session=None):
    try:
        cmd = ['bw', 'get', 'item', item_id]
        if session:
            cmd = ['bw', '--session', session, 'get', 'item', item_id]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print('Bitwarden CLI Fehler:', r.stderr)
            return None
        return json.loads(r.stdout)
    except FileNotFoundError:
        print('Bitwarden CLI (bw) nicht gefunden')
        return None

# Quarantine helper
def quarantine_path(path):
    try:
        p = Path(path)
        if p.exists():
            dest = QUARANTINE_DIR / (p.name + '.' + datetime.utcnow().strftime('%Y%m%d%H%M%S'))
            p.replace(dest)
            return str(dest)
    except Exception as e:
        print('Quarantine Fehler:', e)
    return None

# Actions
def take_immediate_actions(evt):
    # PoC: attempt to isolate network by creating a dummy iptables rule (requires root) - we won't run it automatically in PoC
    print('[friday] Autonome Maßnahmen (PoC): Netzwerk isolieren (simuliert), Prozess beenden (simuliert)')
    # Log action
    cur.execute('INSERT INTO events (ts, type, payload, score, acted) VALUES (?, ?, ?, ?, ?)',
                (datetime.utcnow().isoformat(), 'auto_action', json.dumps(evt), evt.get('score',0.0), 1))
    conn.commit()

# Main monitoring loop (very basic)
def monitor_loop():
    print('[friday] Starte PoC-Monitoring. Drücke STRG+C zum Beenden.')
    try:
        while True:
            # sample CPU per-process spike
            cpu = psutil.cpu_percent(interval=1)
            # simple IO: sum of disk io
            io_counters = psutil.disk_io_counters()
            io_bytes = (io_counters.read_bytes + io_counters.write_bytes) if io_counters else 0
            # naive suspicious network: open connections to unknown ips (PoC: any non-local)
            suspicious_net = False
            conns = psutil.net_connections()
            for c in conns:
                if c.raddr and c.raddr.ip and not c.raddr.ip.startswith('127.') and not c.raddr.ip.startswith('192.168.'):
                    suspicious_net = True
                    break
            evt = {'cpu': cpu, 'io_bytes': io_bytes, 'susp_net': suspicious_net, 'ts': datetime.utcnow().isoformat()}
            score, feat = evaluate_event(evt)
            evt['score'] = score
            # persist event
            cur.execute('INSERT INTO events (ts, type, payload, score) VALUES (?, ?, ?, ?)',
                        (evt['ts'], 'system_sample', json.dumps(evt), score))
            conn.commit()

            if score >= THRESH_AUTONOMOUS:
                print(f"[friday] Kritischer Score {score:.2f} erreicht -> autonome Maßnahme")
                take_immediate_actions(evt)
                # notify user (PoC prints)
            elif score >= THRESH_SUGGEST:
                print(f"[friday] Hoher Score {score:.2f} -> Vorschlag an Benutzer")
                res = prompt_user(f"Verdächtige Aktivität erkannt (Score {score:.2f}). Aktion vorschlagen: Quarantäne-Dateien?", default='später')
                if res in ('ja','j','y'):
                    print('[friday] Benutzer hat genehmigt. Aktion wird ausgeführt (simuliert).')
                    take_immediate_actions(evt)
                else:
                    print('[friday] Aktion verschoben.')
            else:
                # low-risk: output status
                print(f"[friday] Status OK (Score {score:.2f})")

            time.sleep(CONFIG.get('poll_interval', 10))
    except KeyboardInterrupt:
        print('\n[friday] Beendet')

if __name__ == '__main__':
    monitor_loop()
