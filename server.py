from pathlib import Path
from uuid import uuid4
from datetime import date, datetime
import json
import os
import csv
import socket
from flask import Flask, jsonify, request, send_from_directory, redirect, url_for, session
import html as html_lib

BASE_DIR = Path(__file__).resolve().parent
DESKTOP = Path(os.path.expanduser("~/Desktop"))

def pick_writable_dir(candidate_dirs):
    for d in candidate_dirs:
        if not d:
            continue
        try:
            d = Path(d)
            d.mkdir(parents=True, exist_ok=True)
            probe = d / f".probe_{uuid4().hex}"
            with probe.open("w", encoding="utf-8") as f:
                f.write("")
            try:
                probe.unlink()
            except Exception:
                pass
            return d
        except Exception:
            continue
    return BASE_DIR

DATA_DIR = pick_writable_dir([os.getenv("MHT_DATA_DIR"), DESKTOP, BASE_DIR])
CSV_PATH = DATA_DIR / "entries.csv"
HOBBY_CSV_PATH = DATA_DIR / "hobbies.csv"

def load_entries():
    if not CSV_PATH.exists():
        save_entries([])
    try:
        with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []

def save_entries(items):
    fields = [
        "id",
        "date",
        "mood",
        "sleepHours",
        "waterLiters",
        "steps",
        "stressLevel",
        "anxietyLevel",
        "meditationMinutes",
        "screenTimeMinutes",
        "notes",
    ]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in items:
            writer.writerow(row)

def to_iso(d):
    return d.isoformat() if isinstance(d, date) else str(d)

app = Flask(__name__, static_folder=str(Path(".").resolve()))
app.secret_key = os.urandom(24)

def get_lan_ip():
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return None
    finally:
        try:
            if s is not None:
                s.close()
        except Exception:
            pass

def render_layout(title, body):
    return f"""<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8' />
    <meta name='viewport' content='width=device-width, initial-scale=1' />
    <title>{title}</title>
    <link rel='stylesheet' href='/style.css' />
  </head>
  <body>
    <header><h1>Mental Health Tracker</h1></header>
    <main>
      <div class='tabs'>
        <a class='tab' href='/entry'>Entry</a>
        <a class='tab' href='/history'>History</a>
        <a class='tab' href='/dashboard'>Dashboard</a>
        <a class='tab' href='/hobby'>Hobby</a>
        <a class='tab' href='/affirmations'>Affirmations</a>
      </div>
      {body}
    </main>
    <footer><small>Data stored in CSV at Desktop via Python server</small></footer>
  </body>
</html>"""

@app.get("/")
def root():
    ip = get_lan_ip()
    url = f"http://{ip}:8000/" if ip else ""
    mobile = ""
    if url:
        esc = html_lib.escape(url)
        mobile = f"""
        <p><b>Open on your phone (same Wi‑Fi):</b></p>
        <p><a href='{esc}'>{esc}</a></p>
        """
    body = f"""
    <section class='card'>
      <h2>Welcome</h2>
      <p>Select a page above.</p>
      {mobile}
      <p>If it doesn’t open on mobile, allow <b>Python</b> through Windows Firewall (Private network) and keep your phone on the same Wi‑Fi.</p>
    </section>
    """
    return render_layout("Mental Health Tracker", body)

@app.get("/entry")
def entry_page():
    today = date.today().isoformat()
    body = f"""
    <section class='card'>
      <h2>Add / Update Entry</h2>
      <form method='post' action='/entry'>
        <div class='grid'>
          <label><span>Date</span><input type='date' name='date' value='{today}' required /></label>
          <label><span>Mood</span>
            <select name='mood' required>
              <option value=''>Select mood</option>
              <option>Happy</option><option>Neutral</option><option>Sad</option><option>Stressed</option><option>Anxious</option>
            </select>
          </label>
          <label><span>Sleep Hours</span><input type='number' step='0.1' min='0' max='24' name='sleepHours' /></label>
          <label><span>Water Intake (L)</span><input type='number' step='0.1' min='0' name='waterLiters' /></label>
          <label><span>Steps</span><input type='number' step='1' min='0' name='steps' /></label>
          <label><span>Stress (1–10)</span><input type='number' min='1' max='10' name='stressLevel' value='5' /></label>
          <label><span>Anxiety (1–10)</span><input type='number' min='1' max='10' name='anxietyLevel' value='5' /></label>
          <label><span>Meditation (minutes)</span><input type='number' min='0' step='1' name='meditationMinutes' /></label>
          <label><span>Screen Time (minutes)</span><input type='number' min='0' step='1' name='screenTimeMinutes' /></label>
        </div>
        <label class='notes'><span>Notes</span><textarea name='notes' rows='3'></textarea></label>
        <div class='actions'>
          <button type='submit' class='primary'>Save Entry</button>
          <form method='post' action='/entries/clear' style='display:inline'>
            <button type='submit' class='danger'>Clear All</button>
          </form>
        </div>
      </form>
    </section>
    """
    return render_layout("Entry", body)

@app.post("/entry")
def entry_post():
    form = request.form
    payload = {
        "id": form.get("id") or str(uuid4()),
        "date": form.get("date"),
        "mood": form.get("mood", ""),
        "sleepHours": form.get("sleepHours") or "",
        "waterLiters": form.get("waterLiters") or "",
        "steps": form.get("steps") or "",
        "stressLevel": form.get("stressLevel") or "5",
        "anxietyLevel": form.get("anxietyLevel") or "5",
        "meditationMinutes": form.get("meditationMinutes") or "",
        "screenTimeMinutes": form.get("screenTimeMinutes") or "",
        "notes": (form.get("notes") or "").strip(),
    }
    ok, err = validate_payload(payload)
    if not ok:
        session["error"] = err
        return redirect(url_for("entry_page"))
    items = load_entries()
    idx = next((i for i, x in enumerate(items) if x.get("id") == payload["id"]), -1)
    if idx == -1:
        items.append(payload)
    else:
        items[idx] = payload
    save_entries(items)
    session["message"] = "Entry saved"
    return redirect(url_for("history_page"))

@app.get("/history")
def history_page():
    items = load_entries()
    rows = []
    for e in sorted(items, key=lambda x: x.get("date", ""), reverse=True):
        notes = html_lib.escape(e.get("notes", "") or "")
        rows.append(f"""
          <tr>
            <td>{e.get('date','')}</td>
            <td>{e.get('mood','')}</td>
            <td>{e.get('sleepHours','')}</td>
            <td>{e.get('waterLiters','')}</td>
            <td>{e.get('steps','')}</td>
            <td>{e.get('stressLevel','')}</td>
            <td>{e.get('anxietyLevel','')}</td>
            <td>{e.get('meditationMinutes','')}</td>
            <td>{e.get('screenTimeMinutes','')}</td>
            <td>{notes}</td>
            <td>
              <form method='post' action='/entries/delete' style='display:inline'>
                <input type='hidden' name='id' value='{e.get('id','')}' />
                <button type='submit' class='danger'>Delete</button>
              </form>
              <form method='get' action='/entry' style='display:inline'>
                <input type='hidden' name='id' value='{e.get('id','')}' />
                <button type='submit' class='primary'>Edit</button>
              </form>
            </td>
          </tr>
        """)
    body = f"""
    <section class='card'>
      <div class='list-header'>
        <h2>History</h2>
        <div class='list-actions'>
          <form method='post' action='/entries/clear'>
            <button type='submit' class='danger'>Clear All</button>
          </form>
        </div>
      </div>
      <div class='table-wrap'>
        <table>
          <thead><tr>
            <th>Date</th><th>Mood</th><th>Sleep</th><th>Water (L)</th><th>Steps</th>
            <th>Stress</th><th>Anxiety</th><th>Meditation</th><th>Screen Time</th><th>Notes</th><th>Actions</th>
          </tr></thead>
          <tbody>{''.join(rows) if rows else '<tr><td colspan="11">No entries yet</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """
    return render_layout("History", body)


@app.post("/entries/delete")
def entries_delete_post():
    id_ = request.form.get("id")
    items = load_entries()
    items = [x for x in items if x.get("id") != id_]
    save_entries(items)
    return redirect(url_for("history_page"))

@app.post("/entries/clear")
def entries_clear_post():
    save_entries([])
    return redirect(url_for("history_page"))

def compute_weekly_stats():
    items = load_entries()
    parsed = []
    for e in items:
        try:
            d = datetime.fromisoformat(e.get("date")).date()
        except Exception:
            continue
        iso = d.isocalendar()
        parsed.append({
            "iso_year": iso[0],
            "iso_week": iso[1],
            "week_label": f"{iso[0]}-W{str(iso[1]).zfill(2)}",
            "sleepHours": float(e.get("sleepHours") or 0),
            "waterLiters": float(e.get("waterLiters") or 0),
            "steps": int(e.get("steps") or 0),
            "stressLevel": int(e.get("stressLevel") or 0),
            "anxietyLevel": int(e.get("anxietyLevel") or 0),
            "meditationMinutes": int(e.get("meditationMinutes") or 0),
            "screenTimeMinutes": int(e.get("screenTimeMinutes") or 0),
            "date": d.isoformat(),
        })
    agg = {}
    for r in parsed:
        k = (r["iso_year"], r["iso_week"], r["week_label"])
        a = agg.setdefault(k, {
            "week_label": r["week_label"], "start": r["date"], "end": r["date"],
            "sleep_sum": 0.0, "stress_sum": 0, "anxiety_sum": 0, "water_sum": 0.0,
            "meditation_total": 0, "screen_total": 0, "steps_total": 0, "count": 0,
        })
        a["start"] = min(a["start"], r["date"])
        a["end"] = max(a["end"], r["date"])
        a["sleep_sum"] += r["sleepHours"]
        a["stress_sum"] += r["stressLevel"]
        a["anxiety_sum"] += r["anxietyLevel"]
        a["water_sum"] += r["waterLiters"]
        a["meditation_total"] += r["meditationMinutes"]
        a["screen_total"] += r["screenTimeMinutes"]
        a["steps_total"] += r["steps"]
        a["count"] += 1
    out = []
    for _, v in sorted(agg.items(), key=lambda x: x[0]):
        c = max(v["count"], 1)
        out.append({
            "week_label": v["week_label"],
            "start": v["start"],
            "end": v["end"],
            "avg_sleep": round(v["sleep_sum"] / c, 2),
            "avg_stress": round(v["stress_sum"] / c, 2),
            "avg_anxiety": round(v["anxiety_sum"] / c, 2),
            "avg_water": round(v["water_sum"] / c, 2),
            "avg_screen": round(v["screen_total"] / c, 0),
            "total_meditation": v["meditation_total"],
            "total_screen": v["screen_total"],
            "total_steps": v["steps_total"],
        })
    return out

@app.get("/dashboard")
def dashboard_page():
    ws = compute_weekly_stats()
    def svg_line_multi(labels, series, colors, names, width=700, height=260):
        if not series or not labels:
            return ""
        pad_left, pad_right, pad_top, pad_bottom = 50, 10, 20, 40
        inner_w = width - pad_left - pad_right
        inner_h = height - pad_top - pad_bottom
        all_vals = [v for s in series for v in s]
        vmin = min(all_vals)
        vmax = max(all_vals)
        if vmax == vmin:
            vmax = vmin + 1
        def x(i):
            if len(labels) == 1:
                return pad_left + inner_w / 2
            return pad_left + (i * inner_w) / (len(labels) - 1)
        def y(v):
            return pad_top + inner_h - ((v - vmin) * inner_h) / (vmax - vmin)
        x_ticks = []
        for i in range(len(labels)):
            xi = x(i)
            x_ticks.append(f"<line x1='{xi}' y1='{pad_top+inner_h}' x2='{xi}' y2='{pad_top+inner_h+5}' stroke='#bbb'/>")
        axis = f"<line x1='{pad_left}' y1='{pad_top+inner_h}' x2='{pad_left+inner_w}' y2='{pad_top+inner_h}' stroke='#999'/>"
        yaxis = f"<line x1='{pad_left}' y1='{pad_top}' x2='{pad_left}' y2='{pad_top+inner_h}' stroke='#999'/>"
        y_grid = []
        for t in range(5):
            val = vmin + (t * (vmax - vmin)) / 4
            yi = y(val)
            y_grid.append(f"<line x1='{pad_left}' y1='{yi}' x2='{pad_left+inner_w}' y2='{yi}' stroke='#eee'/>")
        series_polylines = []
        markers = []
        for idx, s in enumerate(series):
            pts = " ".join(f"{x(i)},{y(v)}" for i, v in enumerate(s))
            color = colors[idx]
            series_polylines.append(f"<polyline fill='none' stroke='{color}' stroke-width='2' points='{pts}' />")
            for i, v in enumerate(s):
                markers.append(f"<circle cx='{x(i)}' cy='{y(v)}' r='2.5' fill='{color}' />")
        labels_elems = []
        for i in range(len(labels)):
            labels_elems.append(f"<text x='{x(i)}' y='{pad_top+inner_h+18}' font-size='10' text-anchor='middle' fill='#555'>{labels[i]}</text>")
        legend_items = []
        lx = pad_left + 10
        ly = pad_top + 10
        for i, name in enumerate(names):
            color = colors[i]
            legend_items.append(f"<rect x='{lx + i*120}' y='{ly}' width='12' height='12' fill='{color}' />")
            legend_items.append(f"<text x='{lx + i*120 + 18}' y='{ly+11}' font-size='12' fill='#333'>{name}</text>")
        vmin_txt = f"<text x='{pad_left-4}' y='{pad_top+inner_h+18}' font-size='10' text-anchor='end' fill='#555'>{round(vmin,2)}</text>"
        vmax_txt = f"<text x='{pad_left-4}' y='{pad_top+12}' font-size='10' text-anchor='end' fill='#555'>{round(vmax,2)}</text>"
        return f"<svg viewBox='0 0 {width} {height}' width='100%' height='100%' role='img'>{''.join(y_grid)}{axis}{yaxis}{''.join(series_polylines)}{''.join(markers)}{''.join(x_ticks)}{''.join(labels_elems)}{''.join(legend_items)}{vmin_txt}{vmax_txt}</svg>"
    def svg_bar(labels, values, width=700, height=240, fill="#0ea5e9"):
        if not values:
            return ""
        pad_left, pad_right, pad_top, pad_bottom = 50, 10, 20, 40
        inner_w = width - pad_left - pad_right
        inner_h = height - pad_top - pad_bottom
        vmax = max(values) if max(values) > 0 else 1
        n = len(values)
        bar_gap = 8
        bar_w = max(1, (inner_w - (n + 1) * bar_gap) / n)
        bars = []
        axis = f"<line x1='{pad_left}' y1='{pad_top+inner_h}' x2='{pad_left+inner_w}' y2='{pad_top+inner_h}' stroke='#999'/>"
        yaxis = f"<line x1='{pad_left}' y1='{pad_top}' x2='{pad_left}' y2='{pad_top+inner_h}' stroke='#999'/>"
        y_grid = []
        for t in range(5):
            val = (t * vmax) / 4
            yi = pad_top + inner_h - (val * inner_h) / vmax
            y_grid.append(f"<line x1='{pad_left}' y1='{yi}' x2='{pad_left+inner_w}' y2='{yi}' stroke='#eee'/>")
        label_elems = []
        for i, v in enumerate(values):
            x = pad_left + bar_gap + i * (bar_w + bar_gap)
            h = (v * inner_h) / vmax
            y = pad_top + inner_h - h
            bars.append(f"<rect x='{x}' y='{y}' width='{bar_w}' height='{h}' fill='{fill}' />")
            label_elems.append(f"<text x='{x + bar_w/2}' y='{pad_top+inner_h+18}' font-size='10' text-anchor='middle' fill='#555'>{labels[i]}</text>")
        vmax_txt = f"<text x='{pad_left-4}' y='{pad_top+12}' font-size='10' text-anchor='end' fill='#555'>{vmax}</text>"
        return f"<svg viewBox='0 0 {width} {height}' width='100%' height='100%' role='img'>{''.join(y_grid)}{axis}{yaxis}{''.join(bars)}{''.join(label_elems)}{vmax_txt}</svg>"
    rows = []
    for w in ws:
        rows.append(f"""
          <tr>
            <td>{w['week_label']}</td>
            <td>{w['start']}</td>
            <td>{w['end']}</td>
            <td>{w['avg_sleep']}</td>
            <td>{w['avg_stress']}</td>
            <td>{w['avg_anxiety']}</td>
            <td>{w['avg_water']}</td>
            <td>{w['total_meditation']}</td>
            <td>{w['total_screen']}</td>
            <td>{w['avg_screen']}</td>
            <td>{w['total_steps']}</td>
          </tr>
        """)
    labels = [w["week_label"] for w in ws]
    line_multi = svg_line_multi(
        labels,
        [
            [w["avg_sleep"] for w in ws],
            [w["avg_stress"] for w in ws],
            [w["avg_anxiety"] for w in ws],
        ],
        ["#2563eb", "#ef4444", "#7c3aed"],
        ["Sleep", "Stress", "Anxiety"],
    )
    meditation_svg = svg_bar(labels, [w["total_meditation"] for w in ws], fill="#22c55e")
    screen_svg = svg_bar(labels, [w["total_screen"] for w in ws], fill="#f59e0b")
    avg_screen_svg = svg_bar(labels, [w["avg_screen"] for w in ws], fill="#fcd34d")
    steps_svg = svg_bar(labels, [w["total_steps"] for w in ws], fill="#0ea5e9")
    water_svg = svg_bar(labels, [w["avg_water"] for w in ws], fill="#14b8a6")
    charts = ""
    if ws:
        charts = f"""
        <section class='card'>
          <h2>Charts</h2>
          <div class='grid'>
            <div><h3>Avg Sleep / Stress / Anxiety</h3><div class='chart'>{line_multi}</div></div>
            <div><h3>Total Meditation</h3><div class='chart'>{meditation_svg}</div></div>
            <div><h3>Total Screen Time</h3><div class='chart'>{screen_svg}</div></div>
            <div><h3>Avg Screen Time</h3><div class='chart'>{avg_screen_svg}</div></div>
            <div><h3>Total Steps</h3><div class='chart'>{steps_svg}</div></div>
            <div><h3>Avg Water (L)</h3><div class='chart'>{water_svg}</div></div>
          </div>
        </section>
        """
    body = f"""
    <section class='card'>
      <h2>Dashboard (Weekly)</h2>
      <div class='table-wrap'>
        <table>
          <thead><tr>
            <th>Week</th><th>Start</th><th>End</th>
            <th>Avg Sleep</th><th>Avg Stress</th><th>Avg Anxiety</th><th>Avg Water</th>
            <th>Total Meditation</th><th>Total Screen</th><th>Avg Screen</th><th>Total Steps</th>
          </tr></thead>
          <tbody>{''.join(rows) if rows else '<tr><td colspan="11">No entries yet</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    {charts}
    """
    return render_layout("Dashboard", body)

@app.get("/style.css")
def style_css():
    return send_from_directory(app.static_folder, "style.css")

@app.get("/hobby")
def hobby_page():
    items = load_hobbies()
    rows = []
    for h in sorted(items, key=lambda x: x.get("date", ""), reverse=True):
        notes = html_lib.escape(h.get("notes", "") or "")
        rows.append(f"""
          <tr>
            <td>{h.get('date','')}</td>
            <td>{html_lib.escape(h.get('hobbyName',''))}</td>
            <td>{h.get('durationMinutes','')}</td>
            <td>{h.get('satisfactionLevel','')}</td>
            <td>{notes}</td>
            <td>
              <form method='post' action='/hobbies/delete' style='display:inline'>
                <input type='hidden' name='id' value='{h.get('id','')}' />
                <button type='submit' class='danger'>Delete</button>
              </form>
            </td>
          </tr>
        """)
    today = date.today().isoformat()
    body = f"""
    <section class='card'>
      <h2>Hobby Tracker</h2>
      <form method='post' action='/hobby'>
        <div class='grid'>
          <label><span>Date</span><input type='date' name='date' value='{today}' required /></label>
          <label><span>Hobby</span><input type='text' name='hobbyName' required /></label>
          <label><span>Duration (minutes)</span><input type='number' name='durationMinutes' min='0' step='1' /></label>
          <label><span>Satisfaction (1-10)</span><input type='number' name='satisfactionLevel' min='1' max='10' value='5' /></label>
        </div>
        <label class='notes'><span>Notes</span><textarea name='notes' rows='3'></textarea></label>
        <div class='actions'>
          <button type='submit' class='primary'>Save Hobby</button>
          <form method='post' action='/hobbies/clear' style='display:inline'>
            <button type='submit' class='danger'>Clear All</button>
          </form>
        </div>
      </form>
    </section>
    <section class='card'>
      <div class='list-header'><h3>Hobby History</h3></div>
      <div class='table-wrap'>
        <table>
          <thead><tr><th>Date</th><th>Hobby</th><th>Duration</th><th>Satisfaction</th><th>Notes</th><th>Actions</th></tr></thead>
          <tbody>{''.join(rows) if rows else '<tr><td colspan=\"6\">No hobbies yet</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    """
    return render_layout("Hobby", body)

@app.post("/hobby")
def hobby_post():
    form = request.form
    payload = {
        "id": form.get("id") or str(uuid4()),
        "date": form.get("date"),
        "hobbyName": form.get("hobbyName", ""),
        "durationMinutes": form.get("durationMinutes") or "",
        "satisfactionLevel": form.get("satisfactionLevel") or "5",
        "notes": (form.get("notes") or "").strip(),
    }
    ok, err = validate_hobby(payload)
    if not ok:
        session["error"] = err
        return redirect(url_for("hobby_page"))
    items = load_hobbies()
    idx = next((i for i, x in enumerate(items) if x.get("id") == payload["id"]), -1)
    if idx == -1:
        items.append(payload)
    else:
        items[idx] = payload
    save_hobbies(items)
    return redirect(url_for("hobby_page"))

@app.post("/hobbies/delete")
def hobbies_delete_post():
    id_ = request.form.get("id")
    items = load_hobbies()
    items = [x for x in items if x.get("id") != id_]
    save_hobbies(items)
    return redirect(url_for("hobby_page"))

@app.post("/hobbies/clear")
def hobbies_clear_post():
    save_hobbies([])
    return redirect(url_for("hobby_page"))

AFFIRMATIONS = [
    "I believe in my abilities and express my true self with confidence.",
    "I am confident in my skills and talents.",
    "I embrace my uniqueness and share it with the world.",
    "I am capable of achieving my goals.",
    "I am worthy of all the success and happiness that comes my way.",
    "I trust myself to make the right decisions.",
    "I release self-doubt and embrace self-confidence.",
    "I am proud of who I am and what I have accomplished.",
    "I radiate confidence in all that I do.",
    "I am courageous, strong, and resilient.",
    "I choose happiness and positivity every day.",
    "I am grateful for the small joys in my life.",
    "I deserve happiness and welcome it into my life.",
    "My happiness comes from within.",
    "I release negative thoughts and focus on positivity.",
    "I am surrounded by love, joy, and abundance.",
    "I am in control of my own happiness.",
    "I allow myself to feel happy in the present moment.",
    "I create joy in my life through positive choices.",
    "Happiness flows effortlessly into my life.",
    "I love and accept myself exactly as I am.",
    "I am deserving of love and respect from myself and others.",
    "I forgive myself for past mistakes and grow stronger each day.",
    "I am kind to myself and speak positively about myself.",
    "I nurture myself with love and compassion.",
    "I am enough, just as I am.",
    "I am worthy of love, happiness, and fulfillment.",
    "I take care of my mind, body, and spirit with love.",
    "I release self-criticism and embrace self-love.",
    "I honor my body and treat it with respect.",
    "I am resilient and can overcome any challenge.",
    "I turn obstacles into opportunities for growth.",
    "I have the strength to navigate through life’s challenges.",
    "I embrace change and welcome personal growth.",
    "Every setback is an opportunity for me to learn and grow.",
    "I am patient with myself as I grow and evolve.",
    "I trust the process of life and embrace the journey.",
    "I am open to new experiences and personal growth.",
    "I am constantly learning and improving.",
    "I choose to rise above challenges and grow stronger every day.",
    "I am at peace with who I am and where I am in life.",
    "I release tension and stress, embracing calm and peace.",
    "I am present in this moment, fully experiencing it with peace.",
    "I trust that everything is unfolding in perfect timing.",
    "I am grounded, centered, and at peace with myself.",
    "I choose peace over worry and calm over anxiety.",
    "I am in control of my thoughts, and I choose positive ones.",
    "I breathe deeply and release tension with every breath.",
    "I am a beacon of peace and tranquility in all situations.",
    "My mind is calm, and I trust myself to handle whatever comes my way",
]

@app.get("/affirmations")
def affirmations_page():
    idx = session.get("affirm_index", 0)
    quote = AFFIRMATIONS[idx]
    body = f"""
    <section class='card'>
      <h2>Affirmations</h2>
      <div class='affirm-card'><p class='affirm-text'>{html_lib.escape(quote)}</p></div>
      <div class='actions'>
        <form method='post' action='/affirmations/prev'><button class='secondary' type='submit'>Previous</button></form>
        <form method='post' action='/affirmations/random'><button type='submit'>Random</button></form>
        <form method='post' action='/affirmations/next'><button class='secondary' type='submit'>Next</button></form>
      </div>
    </section>
    """
    return render_layout("Affirmations", body)

@app.post("/affirmations/prev")
def affirm_prev():
    idx = session.get("affirm_index", 0)
    idx = (idx - 1) % len(AFFIRMATIONS)
    session["affirm_index"] = idx
    return redirect(url_for("affirmations_page"))

@app.post("/affirmations/next")
def affirm_next():
    idx = session.get("affirm_index", 0)
    idx = (idx + 1) % len(AFFIRMATIONS)
    session["affirm_index"] = idx
    return redirect(url_for("affirmations_page"))

@app.post("/affirmations/random")
def affirm_random():
    import random
    session["affirm_index"] = random.randrange(0, len(AFFIRMATIONS))
    return redirect(url_for("affirmations_page"))

@app.get("/api/entries")
def api_entries_get():
    return jsonify(load_entries())

def load_hobbies():
    if not HOBBY_CSV_PATH.exists():
        save_hobbies([])
    try:
        with HOBBY_CSV_PATH.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []

def save_hobbies(items):
    fields = [
        "id",
        "date",
        "hobbyName",
        "durationMinutes",
        "satisfactionLevel",
        "notes",
    ]
    with HOBBY_CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in items:
            writer.writerow(row)

def validate_payload(p):
    if not p.get("date") or not p.get("mood"):
        return False, "Date and Mood are required"
    try:
        datetime.fromisoformat(str(p.get("date")))
    except Exception:
        return False, "Invalid date format"
    try:
        s = int(p.get("stressLevel", 0))
        a = int(p.get("anxietyLevel", 0))
    except Exception:
        return False, "Stress/Anxiety must be integers"
    if s < 1 or s > 10 or a < 1 or a > 10:
        return False, "Stress/Anxiety must be between 1 and 10"
    return True, None

@app.post("/api/entries")
def api_entries_post():
    payload = request.get_json(force=True) or {}
    ok, err = validate_payload(payload)
    if not ok:
        return jsonify({"error": err}), 400
    items = load_entries()
    payload = {
        "id": payload.get("id") or str(uuid4()),
        "date": to_iso(payload.get("date")),
        "mood": payload.get("mood", ""),
        "sleepHours": float(payload.get("sleepHours") or 0) if payload.get("sleepHours") is not None else "",
        "waterLiters": float(payload.get("waterLiters") or 0) if payload.get("waterLiters") is not None else "",
        "steps": int(payload.get("steps") or 0) if payload.get("steps") is not None else "",
        "stressLevel": int(payload.get("stressLevel", 5)),
        "anxietyLevel": int(payload.get("anxietyLevel", 5)),
        "meditationMinutes": int(payload.get("meditationMinutes") or 0) if payload.get("meditationMinutes") is not None else "",
        "notes": (payload.get("notes") or "").strip(),
    }
    items.append(payload)
    save_entries(items)
    return jsonify(payload), 201

@app.put("/api/entries/<id>")
def api_entries_put(id):
    payload = request.get_json(force=True) or {}
    ok, err = validate_payload(payload)
    if not ok:
        return jsonify({"error": err}), 400
    items = load_entries()
    idx = next((i for i, x in enumerate(items) if x.get("id") == id), -1)
    if idx == -1:
        return jsonify({"error": "Not found"}), 404
    updated = {
        "id": id,
        "date": to_iso(payload.get("date")),
        "mood": payload.get("mood", ""),
        "sleepHours": float(payload.get("sleepHours") or 0) if payload.get("sleepHours") is not None else "",
        "waterLiters": float(payload.get("waterLiters") or 0) if payload.get("waterLiters") is not None else "",
        "steps": int(payload.get("steps") or 0) if payload.get("steps") is not None else "",
        "stressLevel": int(payload.get("stressLevel", 5)),
        "anxietyLevel": int(payload.get("anxietyLevel", 5)),
        "meditationMinutes": int(payload.get("meditationMinutes") or 0) if payload.get("meditationMinutes") is not None else "",
        "notes": (payload.get("notes") or "").strip(),
    }
    items[idx] = updated
    save_entries(items)
    return jsonify(updated)

@app.delete("/api/entries/<id>")
def api_entries_delete(id):
    items = load_entries()
    new_items = [x for x in items if x.get("id") != id]
    if len(new_items) == len(items):
        return jsonify({"error": "Not found"}), 404
    save_entries(new_items)
    return jsonify({"status": "deleted"})

@app.delete("/api/entries")
def api_entries_clear():
    save_entries([])
    return jsonify({"status": "cleared"})

def validate_hobby(p):
    if not p.get("date") or not p.get("hobbyName"):
        return False, "Date and Hobby are required"
    try:
        datetime.fromisoformat(str(p.get("date")))
    except Exception:
        return False, "Invalid date format"
    try:
        s = int(p.get("satisfactionLevel", 0))
    except Exception:
        return False, "Satisfaction must be integer"
    if s < 1 or s > 10:
        return False, "Satisfaction must be between 1 and 10"
    return True, None

@app.get("/api/hobbies")
def api_hobbies_get():
    return jsonify(load_hobbies())

@app.post("/api/hobbies")
def api_hobbies_post():
    payload = request.get_json(force=True) or {}
    ok, err = validate_hobby(payload)
    if not ok:
        return jsonify({"error": err}), 400
    items = load_hobbies()
    obj = {
        "id": payload.get("id") or str(uuid4()),
        "date": str(payload.get("date")),
        "hobbyName": payload.get("hobbyName", ""),
        "durationMinutes": int(payload.get("durationMinutes") or 0) if payload.get("durationMinutes") is not None else "",
        "satisfactionLevel": int(payload.get("satisfactionLevel", 5)),
        "notes": (payload.get("notes") or "").strip(),
    }
    items.append(obj)
    save_hobbies(items)
    return jsonify(obj), 201

@app.put("/api/hobbies/<id>")
def api_hobbies_put(id):
    payload = request.get_json(force=True) or {}
    ok, err = validate_hobby(payload)
    if not ok:
        return jsonify({"error": err}), 400
    items = load_hobbies()
    idx = next((i for i, x in enumerate(items) if x.get("id") == id), -1)
    if idx == -1:
        return jsonify({"error": "Not found"}), 404
    obj = {
        "id": id,
        "date": str(payload.get("date")),
        "hobbyName": payload.get("hobbyName", ""),
        "durationMinutes": int(payload.get("durationMinutes") or 0) if payload.get("durationMinutes") is not None else "",
        "satisfactionLevel": int(payload.get("satisfactionLevel", 5)),
        "notes": (payload.get("notes") or "").strip(),
    }
    items[idx] = obj
    save_hobbies(items)
    return jsonify(obj)

@app.delete("/api/hobbies/<id>")
def api_hobbies_delete(id):
    items = load_hobbies()
    new_items = [x for x in items if x.get("id") != id]
    if len(new_items) == len(items):
        return jsonify({"error": "Not found"}), 404
    save_hobbies(new_items)
    return jsonify({"status": "deleted"})

@app.delete("/api/hobbies")
def api_hobbies_clear():
    save_hobbies([])
    return jsonify({"status": "cleared"})

@app.get("/api/stats/weekly")
def api_stats_weekly():
    items = load_entries()
    parsed = []
    for e in items:
        try:
            d = datetime.fromisoformat(e.get("date")).date()
        except Exception:
            continue
        iso = d.isocalendar()
        parsed.append({
            "iso_year": iso[0],
            "iso_week": iso[1],
            "week_label": f"{iso[0]}-W{str(iso[1]).zfill(2)}",
            "sleepHours": float(e.get("sleepHours") or 0),
            "waterLiters": float(e.get("waterLiters") or 0),
            "steps": int(e.get("steps") or 0),
            "stressLevel": int(e.get("stressLevel") or 0),
            "anxietyLevel": int(e.get("anxietyLevel") or 0),
            "meditationMinutes": int(e.get("meditationMinutes") or 0),
            "date": d.isoformat(),
        })
    agg = {}
    for r in parsed:
        k = (r["iso_year"], r["iso_week"], r["week_label"]) 
        a = agg.setdefault(k, {
            "week_label": r["week_label"],
            "start": r["date"],
            "end": r["date"],
            "sleep_sum": 0.0,
            "stress_sum": 0,
            "anxiety_sum": 0,
            "water_sum": 0.0,
            "meditation_total": 0,
            "steps_total": 0,
            "count": 0,
        })
        a["start"] = min(a["start"], r["date"]) 
        a["end"] = max(a["end"], r["date"]) 
        a["sleep_sum"] += r["sleepHours"]
        a["stress_sum"] += r["stressLevel"]
        a["anxiety_sum"] += r["anxietyLevel"]
        a["water_sum"] += r["waterLiters"]
        a["meditation_total"] += r["meditationMinutes"]
        a["steps_total"] += r["steps"]
        a["count"] += 1
    out = []
    for _, v in sorted(agg.items(), key=lambda x: x[0]):
        c = max(v["count"], 1)
        out.append({
            "week_label": v["week_label"],
            "start": v["start"],
            "end": v["end"],
            "avg_sleep": round(v["sleep_sum"] / c, 2),
            "avg_stress": round(v["stress_sum"] / c, 2),
            "avg_anxiety": round(v["anxiety_sum"] / c, 2),
            "avg_water": round(v["water_sum"] / c, 2),
            "total_meditation": v["meditation_total"],
            "total_steps": v["steps_total"],
        })
    return jsonify(out)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
