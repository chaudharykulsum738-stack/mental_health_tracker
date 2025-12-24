# mental_health_tracker
A Streamlit-based Mental Health Tracker that allows users to log daily mood, sleep, stress, anxiety, hobbies, and view weekly insights using simple data visualization.
# Mental Health Tracker

A simple white–blue web app to log daily mental health metrics, review weekly charts, track hobbies, and browse self‑affirmation flash cards. Data is stored in CSV files on your Desktop via a Python backend.

## Features
- Log: date, mood, sleep hours, water liters, steps, stress/anxiety (1–10), meditation minutes, notes
- History: sortable table with edit and delete
- Dashboard: weekly averages and totals (sleep, stress, anxiety, water, steps, meditation) rendered with Chart.js
- Hobby tracker: date, hobby name, duration, satisfaction (1–10), notes
- Affirmations: flash cards with Previous, Random, Next
- Persisted storage: Desktop CSVs (`entries.csv`, `hobbies.csv`) auto-created with headers

## Requirements
- Python 3.9+ (tested with Python 3.13)
- `Flask` and `streamlit` (pinned in `requirements.txt`)

## Setup
```powershell
# From project root
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If PowerShell script execution is restricted, you can skip activation and use the venv python directly as shown above.

## Run (Web UI)
```powershell
.\.venv\Scripts\python.exe server.py
# or
python server.py
```
Open in your browser:
- `http://127.0.0.1:8000/`

## Run (Streamlit alternative)
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Then open:
- `http://localhost:8501`

## Data Storage
- CSV paths (Desktop):
  - `C:\Users\<your-username>\Desktop\entries.csv`
  - `C:\Users\<your-username>\Desktop\hobbies.csv`
- Auto-created headers on first run:
  - Entries: `id,date,mood,sleepHours,waterLiters,steps,stressLevel,anxietyLevel,meditationMinutes,notes`
  - Hobbies: `id,date,hobbyName,durationMinutes,satisfactionLevel,notes`

## Usage Tips
- Entry: add or update daily metrics; use “Reset Form” to clear.
- History: edit or delete rows; “Clear All” wipes entries.
- Dashboard: switch to visualize weekly review charts.
- Hobby: add, edit, delete; “Clear All” wipes hobbies.
- Affirmations: browse the flash cards; “Random” picks a new card.

## Troubleshooting
- "Running scripts is disabled": run commands via `.venv\Scripts\python.exe` without activating.
- No CSV file: the server auto-creates them; ensure Desktop write access.
