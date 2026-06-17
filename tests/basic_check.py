"""Einfacher Selbsttest für PoC: Simuliert ein Ereignis in der Datenbank"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path(__file__).resolve().parents[1] / 'poc' / 'friday.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("INSERT INTO events (ts, type, payload, score) VALUES (?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), 'test_event', '{"msg":"simuliert"}', 0.9))
conn.commit()
print('Testevent eingefügt')
