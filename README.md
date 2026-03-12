# ReviewTrack — Raspberry Pi Paper Review Dashboard

A full-screen, touch-friendly **PyQt6 dashboard** designed for an **800×480** display on a Raspberry Pi. It helps a researcher track academic paper review invitations, pending reviews, and completed reviews — reading live from a shared SQLite database.

---

## 📸 Overview

The app provides four screens navigated via a sidebar:

| Screen | Description |
|---|---|
| **Dashboard** | Summary stats + recent activity |
| **Invitations** | Pending review invites with Accept / Decline / Abstract buttons |
| **Pending** | Accepted reviews with due dates and portal links |
| **Completed** | All finished reviews |

Key features:
- **Real-time updates** — polls the SQLite database every 5 seconds
- **Kinetic touch scrolling** — finger-flick with smooth momentum via `QScroller`
- **Word-wrapped text** — long titles flow naturally, no horizontal scroll
- **Live log overlay** — in-app log viewer, toggleable via sidebar button
- **EXIT button** — always visible on top-right for quick exit from kiosk mode

---

## 🗂 Project Structure

```
.
├── main.py                    # App entry point, sidebar, navigation, timer
├── ui_components.py           # All screen widgets (Dashboard, Invitations, Pending, Completed)
├── database.py                # SQLite connection and data fetching
├── styles.qss                 # Qt stylesheet — dark navy theme
├── db_schema_reference.md     # Database schema documentation
├── create_dummy_db.py         # Generate a local test database for development
├── deploy.py                  # Deploy app files to Raspberry Pi over SSH
├── create_desktop_shortcut.py # Create a clickable desktop icon on the Pi
├── check_logs.py              # SSH in and tail app.log on the Pi
└── fix_dependencies.py        # Install missing PyQt6 dependencies on the Pi
```

---

## 🗄 Database Schema

The app reads from a SQLite file: `~/.local/share/BackgroundFetcher/reviews.sqlite3`

**Table: `review_items`**

| Column | Type | Description |
|---|---|---|
| `status` | TEXT | `invited`, `accepted`, or `completed` |
| `journal_name` | TEXT | Name of the journal |
| `paper_id` | TEXT | Unique paper identifier |
| `paper_title` | TEXT | Full title of the paper |
| `date_invited` | TEXT | ISO date when invite was received |
| `review_due_date` | TEXT | ISO date when review is due |
| `agree_link` | TEXT | URL to accept the invitation |
| `decline_link` | TEXT | URL to decline the invitation |
| `date_accepted` | TEXT | ISO date when acceptance email was received |
| `manuscript_portal_link` | TEXT | Link to the manuscript review portal |
| `direct_review_link` | TEXT | Direct review URL |
| `date_completed` | TEXT | ISO date when thank-you email was received |
| `last_updated` | TEXT | ISO timestamp of last DB update |

> **Note:** The database uses `PRAGMA journal_mode=WAL` so the background email fetcher can write while the dashboard reads simultaneously.

---

## 🚀 Raspberry Pi Setup

### Prerequisites

- Raspberry Pi running **Raspberry Pi OS** (Bookworm or later recommended)
- Python 3 installed
- A desktop environment (LXDE/Wayfire) with `DISPLAY=:0` active
- Display connected (tested on 800×480 touch screen)

### Install PyQt6 on the Pi

```bash
sudo apt-get update
sudo apt-get install -y python3-pyqt6
```

### Clone / Copy the Project

```bash
git clone https://github.com/YOUR_USERNAME/ReviewTrack.git ~/ReviewerDashboard
cd ~/ReviewerDashboard
```

### Run the App Manually

```bash
export DISPLAY=:0
cd ~/ReviewerDashboard
python3 main.py
```

---

## 🖥 Desktop Shortcut

Run this **once from your Windows PC** (requires `paramiko`) to place a clickable icon on the Pi's desktop:

```bash
pip install paramiko
python create_desktop_shortcut.py
```

This creates `~/Desktop/ReviewTrack.desktop` on the Pi. Double-clicking it will launch the dashboard directly without needing a terminal.

---

## 🛠 Development & Local Testing

### 1. Install dependencies (Windows/Mac/Linux)

```bash
pip install PyQt6 paramiko
```

### 2. Generate a test database

```bash
python create_dummy_db.py
```

This creates a local `reviews.sqlite3` filled with realistic dummy data so you can test the UI without the Pi.

### 3. Run locally

```bash
python main.py
```

> The app will look for the database at `~/.local/share/BackgroundFetcher/reviews.sqlite3` on Linux/Pi, or the local `reviews.sqlite3` as a fallback.

---

## 🚢 Deploying to the Pi

Edit `deploy.py` to set your Pi's IP, username, and password, then run:

```bash
python deploy.py
```

This will:
1. SSH into the Pi
2. Upload `main.py`, `ui_components.py`, `database.py`, `styles.qss`
3. Kill any old instance
4. Start the app in the background (`nohup`) with output logged to `~/ReviewerDashboard/app.log`

### Check Running Logs

```bash
python check_logs.py
```

SSH's into the Pi and prints the latest lines from `app.log`, plus tells you if the process is running.

---

## 🎨 Design Notes

- **Color palette:** Dark navy (`#0a1628`, `#0f1d32`) matching the Stitch prototype
- **Font:** Segoe UI / Inter, 13–14px base for readability on 800×480
- **Sidebar:** 160px fixed-width with emoji navigation icons
- **Touch scrolling:** Qt `QScroller` with kinetic flick + custom `VScrollArea` subclass to enforce viewport width (prevents horizontal scroll)
- **Cards:** `QFrame.review-card` with `setWordWrap(True)` on all title/abstract labels

---

## ⚙️ Configuration

| Variable | File | Default |
|---|---|---|
| Pi IP address | `deploy.py` | `192.168.0.11` |
| Pi username | `deploy.py` | `tahmidrashid` |
| Pi password | `deploy.py` | *(set in file)* |
| Remote app dir | `deploy.py` | `~/ReviewerDashboard` |
| DB path | `database.py` | `~/.local/share/BackgroundFetcher/reviews.sqlite3` |
| Refresh interval | `main.py` | `5000 ms` |

---

## 📋 Requirements

```
PyQt6
paramiko
```

---

## 📄 License

MIT License — free to use and modify.
