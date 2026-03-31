import os
import sys
import json
import time
import subprocess
import threading
from collections import deque
from flask import Flask, render_template, jsonify, request
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Process Manager – runs scripts in background threads, captures logs
# ---------------------------------------------------------------------------
class ProcessManager:
    def __init__(self):
        self.processes = {}
        self.logs = {}
        self.status = {}
        self._lock = threading.Lock()

    def start(self, name, command):
        with self._lock:
            if name in self.processes and self.processes[name].poll() is None:
                return False, "Already running"

            self.logs[name] = deque(maxlen=1000)
            self.status[name] = "running"
            self.logs[name].append(f"[SYSTEM] Starting {name}...")

            try:
                proc = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                )
            except Exception as e:
                self.status[name] = "error"
                self.logs[name].append(f"[ERROR] Failed to start: {e}")
                return False, str(e)

            self.processes[name] = proc
            t = threading.Thread(target=self._read_output, args=(name, proc), daemon=True)
            t.start()
            return True, "Started successfully"

    def _read_output(self, name, proc):
        try:
            for line in proc.stdout:
                stripped = line.rstrip("\n\r")
                if stripped:
                    self.logs[name].append(stripped)
            proc.stdout.close()
        except Exception:
            pass
        proc.wait()
        code = proc.returncode
        self.logs[name].append(f"[SYSTEM] Process exited with code {code}")
        self.status[name] = f"stopped (exit {code})"

    def stop(self, name):
        with self._lock:
            if name in self.processes and self.processes[name].poll() is None:
                try:
                    if sys.platform == "win32":
                        self.processes[name].terminate()
                    else:
                        self.processes[name].terminate()
                    self.logs[name].append("[SYSTEM] Process terminated by user")
                    self.status[name] = "stopped"
                    return True, "Stopped"
                except Exception as e:
                    return False, str(e)
            return False, "Not running"

    def get_status(self, name):
        if name in self.processes:
            if self.processes[name].poll() is None:
                return "running"
        return self.status.get(name, "idle")

    def get_logs(self, name, after=0):
        logs = list(self.logs.get(name, []))
        return logs[after:]

    def get_all_status(self):
        return {name: self.get_status(name) for name in SCRIPTS}


pm = ProcessManager()

SCRIPTS = {
    "scraper":      {"command": [sys.executable, "-u", "job_scraper.py"],  "label": "Job Scraper"},
    "email_finder": {"command": [sys.executable, "-u", "email_finder.py"],"label": "Email Finder"},
    "mailer":       {"command": [sys.executable, "-u", "auto_mailer.py"], "label": "Auto Mailer"},
}

# ---------------------------------------------------------------------------
# Helper – read CSV safely
# ---------------------------------------------------------------------------
def read_csv_safe(path="found_jobs_enriched.csv"):
    full = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if not os.path.exists(full):
        return None
    try:
        return pd.read_csv(full)
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats")
def api_stats():
    df = read_csv_safe()
    if df is None:
        return jsonify({
            "total_jobs": 0,
            "emails_found": 0,
            "emails_sent": 0,
            "emails_pending": 0,
            "no_email": 0,
        })

    total = len(df)
    has_email = df["HR_Email"].notna() & (df["HR_Email"].astype(str).str.strip() != "")
    emails_found = int(has_email.sum())

    sent = 0
    pending = 0
    if "Email_Sent" in df.columns:
        sent = int((df["Email_Sent"] == "Yes").sum())
        pending = int(has_email.sum() - sent)

    return jsonify({
        "total_jobs": total,
        "emails_found": emails_found,
        "emails_sent": sent,
        "emails_pending": pending,
        "no_email": total - emails_found,
    })

@app.route("/api/jobs")
def api_jobs():
    df = read_csv_safe()
    if df is None:
        return jsonify([])
    # Return slim data for the table
    cols = ["Job Title", "Company Name", "Location", "HR_Email", "Email_Sent"]
    cols = [c for c in cols if c in df.columns]
    subset = df[cols].fillna("").head(200)
    return jsonify(subset.to_dict(orient="records"))

@app.route("/api/status")
def api_status():
    return jsonify(pm.get_all_status())

@app.route("/api/start/<script>", methods=["POST"])
def api_start(script):
    if script not in SCRIPTS:
        return jsonify({"ok": False, "msg": "Unknown script"}), 400
    ok, msg = pm.start(script, SCRIPTS[script]["command"])
    return jsonify({"ok": ok, "msg": msg})

@app.route("/api/stop/<script>", methods=["POST"])
def api_stop(script):
    if script not in SCRIPTS:
        return jsonify({"ok": False, "msg": "Unknown script"}), 400
    ok, msg = pm.stop(script)
    return jsonify({"ok": ok, "msg": msg})

@app.route("/api/logs/<script>")
def api_logs(script):
    after = int(request.args.get("after", 0))
    logs = pm.get_logs(script, after)
    return jsonify({"lines": logs, "total": after + len(logs)})

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  JOB APPLICATION BOT – Dashboard")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
