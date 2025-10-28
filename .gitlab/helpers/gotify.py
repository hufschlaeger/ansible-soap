#!/usr/bin/env python3
"""
Gotify Notification Sender for CI/CD Pipelines
Sends test failure notifications to Gotify server
"""

import os
import sys
from pathlib import Path
import requests
from datetime import datetime


def send_gotify_notification():
  """Send notification about failed tests to Gotify"""

  # ===========================================
  # 1. Configuration from Environment Variables
  # ===========================================

  gotify_url = os.getenv("GOTIFY_URL")
  gotify_app_token = os.getenv("GOTIFY_APP_TOKEN")

  if not gotify_url or not gotify_app_token:
    print("❌ Fehler: GOTIFY_URL und GOTIFY_APP_TOKEN müssen gesetzt sein!")
    sys.exit(1)

  # GitLab CI Variables
  ci_commit_short_sha = os.getenv("CI_COMMIT_SHORT_SHA", "unknown")
  ci_pipeline_url = os.getenv("CI_PIPELINE_URL", "")
  ci_project_url = os.getenv("CI_PROJECT_URL", "")
  ci_job_id = os.getenv("CI_JOB_ID", "")
  ci_project_name = os.getenv("CI_PROJECT_NAME", "Project")
  ci_commit_branch = os.getenv("CI_COMMIT_BRANCH", "unknown")
  ci_commit_message = os.getenv("CI_COMMIT_MESSAGE", "")

  # ===========================================
  # 2. Read Failed Tests
  # ===========================================

  failed_tests_file = Path("test-reports/failed-tests.txt")

  if not failed_tests_file.exists():
    print(f"⚠️  Warnung: {failed_tests_file} nicht gefunden")
    failed_tests = "Keine Details verfügbar"
    test_count = 0
  else:
    with open(failed_tests_file, "r", encoding="utf-8") as f:
      content = f.read().strip()
      if not content:
        print("ℹ️  Keine fehlgeschlagenen Tests gefunden")
        return  # Nichts zu senden
      failed_tests = content
      test_count = len([line for line in content.split('\n') if line.strip()])

  # ===========================================
  # 3. Build Message
  # ===========================================

  title = f"🔴 CI Pipeline Fehler - {ci_project_name}"

  # Markdown-formatierte Nachricht
  message_parts = [
    f"**Branch:** `{ci_commit_branch}`",
    f"**Commit:** `{ci_commit_short_sha}`",
  ]

  if ci_commit_message:
    # Erste Zeile der Commit-Message
    first_line = ci_commit_message.split('\n')[0][:100]
    message_parts.append(f"**Message:** {first_line}")

  message_parts.extend([
    f"**Fehlgeschlagene Tests:** {test_count}",
    "",
    "### Details:",
    "```",
    failed_tests[:1000],  # Limitiere auf 1000 Zeichen
    "```"
  ])

  if len(failed_tests) > 1000:
    message_parts.append("\n_... (gekürzt)_")

  message = "\n".join(message_parts)

  # ===========================================
  # 4. Build Payload
  # ===========================================

  payload = {
    "title": title,
    "message": message,
    "priority": 8,  # Hohe Priorität für Fehler
    "extras": {
      "client::display": {
        "contentType": "text/markdown"
      },
      "client::notification": {
        "click": {
          "url": ci_pipeline_url or ci_project_url
        }
      },
      # Custom metadata
      "gitlab": {
        "commit": ci_commit_short_sha,
        "branch": ci_commit_branch,
        "pipeline_url": ci_pipeline_url,
        "job_id": ci_job_id,
        "project": ci_project_name,
        "timestamp": datetime.utcnow().isoformat()
      }
    }
  }

  # ===========================================
  # 5. Send Request
  # ===========================================

  try:
    print(f"📤 Sende Benachrichtigung an {gotify_url}")
    print(f"   Tests fehlgeschlagen: {test_count}")
    print(f"   Commit: {ci_commit_short_sha} ({ci_commit_branch})")

    response = requests.post(
      f"{gotify_url}/message",
      params={"token": gotify_app_token},
      json=payload,
      timeout=10,
      # verify=True ist default - requests verwendet certifi automatisch
    )

    response.raise_for_status()

    print(f"✅ Benachrichtigung erfolgreich gesendet!")
    print(f"   Response: {response.status_code}")
    print(f"   Message ID: {response.json().get('id', 'unknown')}")

  except requests.exceptions.SSLError as e:
    print(f"❌ SSL-Fehler: {e}")
    print("💡 Tipp: Überprüfe das SSL-Zertifikat des Gotify-Servers")
    sys.exit(1)

  except requests.exceptions.ConnectionError as e:
    print(f"❌ Verbindungsfehler: {e}")
    print(f"💡 Tipp: Ist {gotify_url} erreichbar?")
    sys.exit(1)

  except requests.exceptions.Timeout as e:
    print(f"❌ Timeout: {e}")
    sys.exit(1)

  except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP-Fehler: {e}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    sys.exit(1)

  except Exception as e:
    print(f"❌ Unerwarteter Fehler: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def main():
  """Main entry point"""

  # Debug-Modus
  if "--debug" in sys.argv:
    print("=== Debug Information ===")
    print(f"GOTIFY_URL: {os.getenv('GOTIFY_URL', 'NOT SET')}")
    print(f"GOTIFY_APP_TOKEN: {'SET' if os.getenv('GOTIFY_APP_TOKEN') else 'NOT SET'}")
    print(f"CI_COMMIT_SHORT_SHA: {os.getenv('CI_COMMIT_SHORT_SHA', 'NOT SET')}")
    print(f"CI_PIPELINE_URL: {os.getenv('CI_PIPELINE_URL', 'NOT SET')}")
    print(f"Working Directory: {os.getcwd()}")
    print()

  # SSL Debug
  if "--ssl-debug" in sys.argv:
    import ssl
    import certifi
    print("=== SSL Configuration ===")
    print(f"OpenSSL Version: {ssl.OPENSSL_VERSION}")
    print(f"Certifi Bundle: {certifi.where()}")
    paths = ssl.get_default_verify_paths()
    print(f"Default cafile: {paths.cafile}")
    print(f"Default capath: {paths.capath}")
    print()

  send_gotify_notification()


if __name__ == "__main__":
  main()
