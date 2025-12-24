from pathlib import Path
from uuid import uuid4
from datetime import date, datetime
import json
import os
import shutil
import csv
import streamlit as st
import pandas as pd

DESKTOP = Path(os.path.expanduser("~/Desktop"))
DESKTOP.mkdir(parents=True, exist_ok=True)
JSON_PATH = DESKTOP / "entries.json"
CSV_PATH = DESKTOP / "entries.csv"
HOBBY_CSV_PATH = DESKTOP / "hobbies.csv"

def load_entries():
    if CSV_PATH.exists():
        try:
            with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception:
            return []
    root_json = Path("entries.json")
    src = None
    if root_json.exists():
        src = root_json
    elif JSON_PATH.exists():
        src = JSON_PATH
    if src is not None:
        try:
            with src.open("r", encoding="utf-8") as f:
                data = json.load(f)
            save_entries(data)
            try:
                shutil.move(str(src), str(JSON_PATH))
            except Exception:
                pass
            return data
        except Exception:
            return []
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
        "notes",
    ]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in items:
            writer.writerow(row)

# Ensure CSV exists with headers on first run
if not CSV_PATH.exists():
    save_entries([])
if not HOBBY_CSV_PATH.exists():
    with HOBBY_CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "date", "hobbyName", "durationMinutes", "satisfactionLevel", "notes"],
        )
        writer.writeheader()

def load_hobbies():
    try:
        with HOBBY_CSV_PATH.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []

def save_hobbies(items):
    fields = ["id", "date", "hobbyName", "durationMinutes", "satisfactionLevel", "notes"]
    with HOBBY_CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in items:
            writer.writerow(row)

def to_iso(d):
    return d.isoformat() if isinstance(d, date) else str(d)

def default_values():
    return {
        "date": date.today(),
        "mood": "",
        "sleep": 0.0,
        "water": 0.0,
        "steps": 0,
        "stress": 5,
        "anxiety": 5,
        "meditation": 0,
        "notes": "",
    }

st.set_page_config(page_title="Mental Health Tracker", page_icon="🧠", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
      background: radial-gradient(1200px 800px at 20% -10%, rgba(59,130,246,0.12), transparent 60%),
                  radial-gradient(1200px 800px at 90% 10%, rgba(14,165,233,0.14), transparent 55%),
                  linear-gradient(180deg, #ffffff 0%, #f5f8ff 100%);
    }
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1100px; }
    .banner { text-align:center; padding: 12px 12px; margin: 0 0 8px; font-size: 30px; font-weight: 800; letter-spacing:-0.02em; background: linear-gradient(90deg,#3b82f6,#0ea5e9); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .metric-row { margin-bottom: 8px; }
    .badge { display:inline-flex; align-items:center; gap:6px; padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(226,232,240,1); font-weight:700; font-size:12px; background: rgba(255,255,255,0.85); }
    .badge.happy { color:#16a34a; border-color:#bbf7d0; }
    .badge.neutral { color:#2563eb; border-color:#bfdbfe; }
    .badge.sad { color:#60a5fa; border-color:#bfdbfe; }
    .badge.stressed { color:#f59e0b; border-color:#fde68a; }
    .badge.anxious { color:#ef4444; border-color:#fecaca; }
    .entry-card { border: 1px solid rgba(226,232,240,1); background: rgba(248,250,252,0.9); border-radius: 14px; padding: 12px; margin: 10px 0; box-shadow: 0 10px 28px rgba(15,23,42,0.08); }
    .entry-top { display:flex; align-items:center; justify-content:space-between; }
    .entry-grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 10px; margin-top: 8px; }
    .entry-kv { color:#475569; font-size: 13px; }
    .entry-kv b { color:#0f172a; }

    [data-testid="stMetric"] { background: rgba(248,250,252,0.9); border: 1px solid rgba(226,232,240,1); border-radius: 14px; padding: 12px 14px; box-shadow: 0 10px 28px rgba(15,23,42,0.08); }
    [data-testid="stMetricValue"] { color:#0f172a; }
    [data-testid="stMetricLabel"] { color:#475569; }

    div.stButton>button { border-radius: 12px; border: 1px solid rgba(226,232,240,1); background: rgba(255,255,255,0.92); color:#0f172a; }
    div.stButton>button:hover { border-color: rgba(59,130,246,0.55); box-shadow: 0 10px 28px rgba(59,130,246,0.14); transform: translateY(-1px); }
    div.stButton>button:active { transform: translateY(1px); }

    .stTabs [data-baseweb="tab-list"] { gap: 10px; padding: 8px; border-radius: 16px; background: rgba(255,255,255,0.65); border: 1px solid rgba(226,232,240,1); }
    .stTabs [data-baseweb="tab"] { border-radius: 999px; padding: 8px 12px; background: rgba(255,255,255,0.8); border: 1px solid rgba(226,232,240,1); }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, rgba(234,242,255,1) 0%, rgba(224,242,254,1) 100%); border-color: rgba(59,130,246,0.45); }

    .affirm-card { border: 1px solid rgba(226,232,240,1); background: linear-gradient(135deg, rgba(234,242,255,1) 0%, rgba(240,249,255,1) 100%); border-radius: 18px; padding: 18px; margin: 10px 0; text-align:center; font-size: 20px; color:#0b132b; box-shadow: 0 10px 28px rgba(59,130,246,0.14); }
    </style>
    """,
    unsafe_allow_html=True,
)

if "editing_id" not in st.session_state:
    st.session_state.editing_id = None
if "form" not in st.session_state:
    st.session_state.form = default_values()
if "celebrate" not in st.session_state:
    st.session_state.celebrate = False
if "hobby_editing_id" not in st.session_state:
    st.session_state.hobby_editing_id = None
if "hobby_form" not in st.session_state:
    st.session_state.hobby_form = {
        "date": date.today(),
        "hobbyName": "",
        "durationMinutes": 0,
        "satisfactionLevel": 5,
        "notes": "",
    }
if "affirm_index" not in st.session_state:
    st.session_state.affirm_index = 0

entries = load_entries()
hobbies = load_hobbies()

if st.session_state.celebrate:
    st.balloons()
    st.session_state.celebrate = False

def mood_class(m):
    m = (m or "").lower()
    if m == "happy":
        return "happy"
    if m == "neutral":
        return "neutral"
    if m == "sad":
        return "sad"
    if m == "stressed":
        return "stressed"
    if m == "anxious":
        return "anxious"
    return ""

def stats(entries):
    n = len(entries)
    if n == 0:
        return {
            "count": 0,
            "avg_sleep": 0.0,
            "avg_stress": 0.0,
            "avg_anxiety": 0.0,
            "meditation_total": 0,
        }
    s = sum(float(e.get("sleepHours", 0) or 0) for e in entries)
    stv = sum(int(e.get("stressLevel", 0) or 0) for e in entries)
    anx = sum(int(e.get("anxietyLevel", 0) or 0) for e in entries)
    med = sum(int(e.get("meditationMinutes", 0) or 0) for e in entries)
    return {
        "count": n,
        "avg_sleep": round(s / n, 2),
        "avg_stress": round(stv / n, 2),
        "avg_anxiety": round(anx / n, 2),
        "meditation_total": med,
    }

def weekly_stats_df(entries):
    if not entries:
        return pd.DataFrame()
    df = pd.DataFrame(entries)
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    df = df.dropna(subset=["date"]) 
    for col in [
        "sleepHours",
        "waterLiters",
        "steps",
        "stressLevel",
        "anxietyLevel",
        "meditationMinutes",
    ]:
        df[col] = pd.to_numeric(df.get(col), errors="coerce")
    iso = df["date"].dt.isocalendar()
    df["iso_year"] = iso["year"]
    df["iso_week"] = iso["week"]
    df["week_label"] = df["iso_year"].astype(str) + "-W" + df["iso_week"].astype(str).str.zfill(2)
    g = df.groupby(["iso_year", "iso_week", "week_label"], dropna=False)
    agg = g.agg(
        avg_sleep=("sleepHours", "mean"),
        avg_stress=("stressLevel", "mean"),
        avg_anxiety=("anxietyLevel", "mean"),
        avg_water=("waterLiters", "mean"),
        total_meditation=("meditationMinutes", "sum"),
        total_steps=("steps", "sum"),
        start=("date", "min"),
        end=("date", "max"),
    )
    agg = agg.sort_values(["iso_year", "iso_week"]).reset_index()
    return agg

st.markdown('<div class="banner">🧠 Mental Health Tracker</div>', unsafe_allow_html=True)
ms = stats(entries)
mc1, mc2, mc3, mc4 = st.columns(4)
with mc1:
    st.metric("Entries", ms["count"]) 
with mc2:
    st.metric("Avg Sleep", f"{ms['avg_sleep']} h")
with mc3:
    st.metric("Avg Stress", ms["avg_stress"]) 
with mc4:
    st.metric("Meditation Total", f"{ms['meditation_total']} min")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Log Entry", "History", "Dashboard", "Hobby", "Affirmations"])
with tab1:
    st.subheader("Add / Update Entry")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.form["date"] = st.date_input("Date", st.session_state.form.get("date", date.today()))
        st.session_state.form["sleep"] = st.number_input("Sleep Hours", min_value=0.0, max_value=24.0, step=0.1, value=float(st.session_state.form.get("sleep", 0.0)))
        st.session_state.form["steps"] = st.number_input("Steps", min_value=0, step=1, value=int(st.session_state.form.get("steps", 0)))
        st.session_state.form["stress"] = st.slider("Stress Level (1–10)", min_value=1, max_value=10, value=int(st.session_state.form.get("stress", 5)))
        st.session_state.form["meditation"] = st.number_input("Meditation (minutes)", min_value=0, step=1, value=int(st.session_state.form.get("meditation", 0)))
    with c2:
        st.session_state.form["mood"] = st.selectbox("Mood", ["", "Happy", "Neutral", "Sad", "Stressed", "Anxious"], index=["", "Happy", "Neutral", "Sad", "Stressed", "Anxious"].index(st.session_state.form.get("mood", "")))
        st.session_state.form["water"] = st.number_input("Water Intake (Liters)", min_value=0.0, step=0.1, value=float(st.session_state.form.get("water", 0.0)))
        st.session_state.form["anxiety"] = st.slider("Anxiety Level (1–10)", min_value=1, max_value=10, value=int(st.session_state.form.get("anxiety", 5)))
        st.session_state.form["notes"] = st.text_area("Notes", value=st.session_state.form.get("notes", ""), height=100)

    cols = st.columns(3)
    save_label = "Update Entry" if st.session_state.editing_id else "Save Entry"
    if cols[0].button(save_label):
        payload = {
            "id": st.session_state.editing_id or str(uuid4()),
            "date": to_iso(st.session_state.form["date"]),
            "mood": st.session_state.form["mood"],
            "sleepHours": float(st.session_state.form["sleep"]),
            "waterLiters": float(st.session_state.form["water"]),
            "steps": int(st.session_state.form["steps"]),
            "stressLevel": int(st.session_state.form["stress"]),
            "anxietyLevel": int(st.session_state.form["anxiety"]),
            "meditationMinutes": int(st.session_state.form["meditation"]),
            "notes": st.session_state.form["notes"].strip(),
        }
        if payload["date"] == "" or payload["mood"] == "":
            st.error("Date and Mood are required")
        elif payload["stressLevel"] < 1 or payload["stressLevel"] > 10 or payload["anxietyLevel"] < 1 or payload["anxietyLevel"] > 10:
            st.error("Stress/Anxiety must be between 1 and 10")
        else:
            if st.session_state.editing_id:
                idx = next((i for i, x in enumerate(entries) if x["id"] == st.session_state.editing_id), -1)
                if idx != -1:
                    entries[idx] = payload
                st.success("Entry updated")
            else:
                entries.append(payload)
                st.success("Entry saved")
            save_entries(entries)
            st.session_state.editing_id = None
            st.session_state.form = default_values()
            st.session_state.celebrate = True
            st.rerun()
    if cols[1].button("Reset Form"):
        st.session_state.editing_id = None
        st.session_state.form = default_values()
        st.rerun()
    if cols[2].button("Clear All"):
        entries = []
        save_entries(entries)
        st.session_state.editing_id = None
        st.session_state.form = default_values()
        st.success("History cleared")
        st.rerun()

with tab2:
    st.subheader("History")
    if entries:
        sorted_entries = sorted(entries, key=lambda e: e.get("date", ""), reverse=True)
        display_rows = [{
            "Date": e.get("date", ""),
            "Mood": e.get("mood", ""),
            "Sleep": e.get("sleepHours", ""),
            "Water (L)": e.get("waterLiters", ""),
            "Steps": e.get("steps", ""),
            "Stress": e.get("stressLevel", ""),
            "Anxiety": e.get("anxietyLevel", ""),
            "Meditation": e.get("meditationMinutes", ""),
            "Notes": e.get("notes", ""),
            "id": e.get("id", ""),
        } for e in sorted_entries]
        st.dataframe([{k: v for k, v in row.items() if k != "id"} for row in display_rows], width="stretch")
        for row in display_rows:
            st.markdown(
                f"""
                <div class="entry-card">
                    <div class="entry-top">
                        <span class="badge {mood_class(row['Mood'])}">{row['Mood']}</span>
                        <div class="entry-kv"><b>{row['Date']}</b></div>
                    </div>
                    <div class="entry-grid">
                        <div class="entry-kv">Sleep: <b>{row['Sleep']}</b></div>
                        <div class="entry-kv">Water: <b>{row['Water (L)']} L</b></div>
                        <div class="entry-kv">Steps: <b>{row['Steps']}</b></div>
                        <div class="entry-kv">Stress: <b>{row['Stress']}</b></div>
                        <div class="entry-kv">Anxiety: <b>{row['Anxiety']}</b></div>
                        <div class="entry-kv">Meditation: <b>{row['Meditation']} min</b></div>
                    </div>
                    <div class="entry-kv">Notes: <b>{row['Notes']}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            if c1.button("Edit", key=f"edit_{row['id']}"):
                st.session_state.editing_id = row["id"]
                e = next((x for x in entries if x["id"] == row["id"]), None)
                if e:
                    st.session_state.form = {
                        "date": datetime.fromisoformat(e.get("date", date.today().isoformat())).date(),
                        "mood": e.get("mood", ""),
                        "sleep": float(e.get("sleepHours", 0.0)),
                        "water": float(e.get("waterLiters", 0.0)),
                        "steps": int(e.get("steps", 0)),
                        "stress": int(e.get("stressLevel", 5)),
                        "anxiety": int(e.get("anxietyLevel", 5)),
                        "meditation": int(e.get("meditationMinutes", 0)),
                        "notes": e.get("notes", ""),
                    }
                st.rerun()
            if c2.button("Delete", key=f"del_{row['id']}"):
                entries = [x for x in entries if x["id"] != row["id"]]
                save_entries(entries)
                if st.session_state.editing_id == row["id"]:
                    st.session_state.editing_id = None
                    st.session_state.form = default_values()
                st.success("Entry deleted")
                st.rerun()
    else:
        st.info("No entries yet")

with tab3:
    st.subheader("Dashboard")
    ws = weekly_stats_df(entries)
    if ws.empty:
        st.info("No entries yet")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.line_chart(ws.set_index("week_label")[["avg_sleep", "avg_stress", "avg_anxiety"]])
        with c2:
            st.bar_chart(ws.set_index("week_label")["total_meditation"])
        st.bar_chart(ws.set_index("week_label")["total_steps"])
        st.bar_chart(ws.set_index("week_label")["avg_water"])
        st.dataframe(
            ws[[
                "week_label",
                "start",
                "end",
                "avg_sleep",
                "avg_stress",
                "avg_anxiety",
                "avg_water",
                "total_meditation",
                "total_steps",
            ]]
        )

with tab4:
    st.subheader("Hobby Tracker")
    hc1, hc2 = st.columns(2)
    with hc1:
        st.session_state.hobby_form["date"] = st.date_input("Date", st.session_state.hobby_form.get("date", date.today()), key="hobby_date")
        st.session_state.hobby_form["hobbyName"] = st.text_input("Hobby", st.session_state.hobby_form.get("hobbyName", ""), key="hobby_name")
        st.session_state.hobby_form["durationMinutes"] = st.number_input("Duration (minutes)", min_value=0, step=1, value=int(st.session_state.hobby_form.get("durationMinutes", 0)), key="hobby_duration")
        st.session_state.hobby_form["satisfactionLevel"] = st.slider("Satisfaction (1–10)", min_value=1, max_value=10, value=int(st.session_state.hobby_form.get("satisfactionLevel", 5)), key="hobby_satisfaction")
        st.session_state.hobby_form["notes"] = st.text_area("Notes", value=st.session_state.hobby_form.get("notes", ""), height=100, key="hobby_notes")
        hcols = st.columns(3)
        h_save_label = "Update Hobby" if st.session_state.hobby_editing_id else "Save Hobby"
        if hcols[0].button(h_save_label, key="hobby_save_btn"):
            payload = {
                "id": st.session_state.hobby_editing_id or str(uuid4()),
                "date": to_iso(st.session_state.hobby_form["date"]),
                "hobbyName": st.session_state.hobby_form["hobbyName"].strip(),
                "durationMinutes": int(st.session_state.hobby_form["durationMinutes"]),
                "satisfactionLevel": int(st.session_state.hobby_form["satisfactionLevel"]),
                "notes": st.session_state.hobby_form["notes"].strip(),
            }
            if not payload["date"] or not payload["hobbyName"]:
                st.error("Date and Hobby are required")
            elif payload["satisfactionLevel"] < 1 or payload["satisfactionLevel"] > 10:
                st.error("Satisfaction must be between 1 and 10")
            else:
                if st.session_state.hobby_editing_id:
                    idx = next((i for i, x in enumerate(hobbies) if x["id"] == st.session_state.hobby_editing_id), -1)
                    if idx != -1:
                        hobbies[idx] = payload
                    st.success("Hobby updated")
                else:
                    hobbies.append(payload)
                    st.success("Hobby saved")
                save_hobbies(hobbies)
                st.session_state.hobby_editing_id = None
                st.session_state.hobby_form = {
                    "date": date.today(),
                    "hobbyName": "",
                    "durationMinutes": 0,
                    "satisfactionLevel": 5,
                    "notes": "",
                }
                st.rerun()
        if hcols[1].button("Reset", key="hobby_reset_btn"):
            st.session_state.hobby_editing_id = None
            st.session_state.hobby_form = {
                "date": date.today(),
                "hobbyName": "",
                "durationMinutes": 0,
                "satisfactionLevel": 5,
                "notes": "",
            }
            st.rerun()
        if hcols[2].button("Clear All", key="hobby_clear_btn"):
            hobbies = []
            save_hobbies(hobbies)
            st.session_state.hobby_editing_id = None
            st.session_state.hobby_form = {
                "date": date.today(),
                "hobbyName": "",
                "durationMinutes": 0,
                "satisfactionLevel": 5,
                "notes": "",
            }
            st.success("Hobby history cleared")
            st.rerun()
    with hc2:
        st.subheader("Hobby History")
        if hobbies:
            sorted_h = sorted(hobbies, key=lambda e: e.get("date", ""), reverse=True)
            for h in sorted_h:
                st.markdown(
                    f"""
                    <div class="entry-card">
                        <div class="entry-top">
                            <div class="entry-kv"><b>{h.get('date','')}</b></div>
                            <span class="badge neutral">{(h.get('hobbyName',''))}</span>
                        </div>
                        <div class="entry-grid">
                            <div class="entry-kv">Duration: <b>{h.get('durationMinutes','')} min</b></div>
                            <div class="entry-kv">Satisfaction: <b>{h.get('satisfactionLevel','')}</b></div>
                        </div>
                        <div class="entry-kv">Notes: <b>{h.get('notes','')}</b></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                hc_edit, hc_del = st.columns(2)
                if hc_edit.button("Edit", key=f"h_edit_{h['id']}"):
                    st.session_state.hobby_editing_id = h["id"]
                    st.session_state.hobby_form = {
                        "date": datetime.fromisoformat(h.get("date", date.today().isoformat())).date(),
                        "hobbyName": h.get("hobbyName", ""),
                        "durationMinutes": int(h.get("durationMinutes", 0) or 0),
                        "satisfactionLevel": int(h.get("satisfactionLevel", 5) or 5),
                        "notes": h.get("notes", ""),
                    }
                    st.rerun()
                if hc_del.button("Delete", key=f"h_del_{h['id']}"):
                    hobbies = [x for x in hobbies if x["id"] != h["id"]]
                    save_hobbies(hobbies)
                    if st.session_state.hobby_editing_id == h["id"]:
                        st.session_state.hobby_editing_id = None
                        st.session_state.hobby_form = {
                            "date": date.today(),
                            "hobbyName": "",
                            "durationMinutes": 0,
                            "satisfactionLevel": 5,
                            "notes": "",
                        }
                    st.success("Hobby deleted")
                    st.rerun()

with tab5:
    st.subheader("Affirmations")
    affirmations = [
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
    st.info("Use the buttons to navigate affirmations")
    st.write(
        f"""
        <div class="affirm-card">
            {affirmations[st.session_state.affirm_index]}
        </div>
        """,
        unsafe_allow_html=True,
    )
    ac1, ac2, ac3 = st.columns(3)
    if ac1.button("Previous"):
        st.session_state.affirm_index = (st.session_state.affirm_index - 1) % len(affirmations)
        st.rerun()
    if ac2.button("Random"):
        st.session_state.affirm_index = int(pd.Series(range(len(affirmations))).sample(1).iloc[0])
        st.rerun()
    if ac3.button("Next"):
        st.session_state.affirm_index = (st.session_state.affirm_index + 1) % len(affirmations)
        st.rerun()

