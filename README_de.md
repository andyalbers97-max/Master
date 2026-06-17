# friday-agent PoC (Deutsch)

Dieses Repository enthält einen Proof-of-Concept (PoC) für "friday": einen lokal laufenden, lernfähigen, interaktiven System-Agenten zur Überwachung, Sicherheitsreaktion und Geheimnisverwaltung.

Kurzbeschreibung
- Ziel: Lokaler Agent, der Systemzustand überwacht, Vorschläge macht und vor geplanten Aktionen mit dem Benutzer interagiert. In konfigurierbaren, eindeutig definierten Notfällen kann er autonom handeln.
- Lernfähigkeit: On-device inkrementelles Lernen (Labels durch Nutzer) zur Verbesserung der Scoring-Logik.
- Passwort-Funktionen: Integration mit Passwort-Managern (Bitwarden CLI, KeePass) zur sicheren Auflistung, Anzeige (nur nach Master-Passwort) und optionalen Rotation über offizielle APIs/CLI.

Wichtig: Dieses PoC führt keine heimliche Passworteinsicht durch — jede Aktion erfordert ausdrückliche Zustimmung des Besitzers (außer bei konfiguriertem Notfallmodus).

Dateien im Branch
- README_de.md (dieses Dokument)
- poc/agent.py (PoC-Agent)
- config/example.yaml (Beispielkonfiguration)
- systemd/friday-agent.service (systemd-Service-Datei für Linux)
- scripts/install.sh (Installationshilfe)
- tests/basic_check.py (einfacher Selbsttest)

Voraussetzungen (PoC, Linux empfohlen)
- Python 3.8+
- optional: bw (Bitwarden CLI) falls Bitwarden-Integration genutzt wird
- optional: pykeepass falls KeePass-Integration genutzt wird
- empfohlen: virtualenv

Nächste Schritte
- Schau dir poc/agent.py an und gib Feedback. Ich passe Integrationen (Windows Defender, ClamAV, u.ä.) an, sobald du bestätigst welches OS priorisiert werden soll.
