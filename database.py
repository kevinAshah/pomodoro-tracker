import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / ".pomodoro_tracker" / "pomodoro.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Segments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#3498db',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Pomodoro sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            segment_id INTEGER NOT NULL,
            description TEXT,
            duration_minutes INTEGER DEFAULT 25,
            focus_rating INTEGER DEFAULT 3,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (segment_id) REFERENCES segments(id)
        )
    """)
    
    # Insert 5 fixed segments
    default_segments = [
        ("Work", "#e74c3c"),      # 🔴 Red - Office/Job work
        ("Solve", "#f39c12"),     # 🟡 Orange - Problem solving (DSA, Math, System Design)
        ("Build", "#2ecc71"),     # 🟢 Green - Building side projects
        ("Learn", "#3498db"),     # 🔵 Blue - Upskilling, learning new concepts
        ("Chill", "#9b59b6"),     # 🟣 Purple - Netflix, YouTube, leisure
    ]
    
    for name, color in default_segments:
        cursor.execute(
            "INSERT OR IGNORE INTO segments (name, color) VALUES (?, ?)",
            (name, color)
        )
    
    conn.commit()
    conn.close()


def get_segments() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, color FROM segments ORDER BY id")
    segments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return segments


def add_segment(name: str, color: str = "#3498db") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO segments (name, color) VALUES (?, ?)",
        (name, color)
    )
    segment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return segment_id


def save_session(
    segment_id: int,
    description: str,
    duration_minutes: int,
    started_at: datetime,
    focus_rating: int = 3
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sessions (segment_id, description, duration_minutes, started_at, focus_rating)
        VALUES (?, ?, ?, ?, ?)
        """,
        (segment_id, description, duration_minutes, started_at.isoformat(), focus_rating)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_today_sessions() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        SELECT s.*, seg.name as segment_name, seg.color as segment_color
        FROM sessions s
        JOIN segments seg ON s.segment_id = seg.id
        WHERE date(s.completed_at) = ?
        ORDER BY s.started_at ASC
        """,
        (today,)
    )
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions


def get_time_segment(hour: int) -> str:
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 24:
        return "evening"
    else:  # 0 <= hour < 6
        return "midnight"


def get_today_sessions_by_time_segment() -> dict:
    sessions = get_today_sessions()
    
    time_segments = {
        "morning": {"label": "Morning (6 AM - 12 PM)", "sessions": [], "count": 0, "minutes": 0},
        "afternoon": {"label": "Afternoon (12 PM - 6 PM)", "sessions": [], "count": 0, "minutes": 0},
        "evening": {"label": "Evening (6 PM - 12 AM)", "sessions": [], "count": 0, "minutes": 0},
        "midnight": {"label": "Midnight (12 AM - 6 AM)", "sessions": [], "count": 0, "minutes": 0},
    }
    
    for session in sessions:
        started_at = datetime.fromisoformat(session["started_at"])
        hour = started_at.hour
        segment = get_time_segment(hour)
        
        time_segments[segment]["sessions"].append(session)
        time_segments[segment]["count"] += 1
        time_segments[segment]["minutes"] += session["duration_minutes"]
    
    return time_segments


def get_sessions_by_date_range(start_date: str, end_date: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.*, seg.name as segment_name, seg.color as segment_color
        FROM sessions s
        JOIN segments seg ON s.segment_id = seg.id
        WHERE date(s.completed_at) BETWEEN ? AND ?
        ORDER BY s.completed_at DESC
        """,
        (start_date, end_date)
    )
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions


def get_today_stats() -> dict:
    sessions = get_today_sessions()
    
    total_minutes = sum(s["duration_minutes"] for s in sessions)
    total_pomodoros = len(sessions)
    
    segment_stats = {}
    for session in sessions:
        seg_name = session["segment_name"]
        if seg_name not in segment_stats:
            segment_stats[seg_name] = {
                "name": seg_name,
                "color": session["segment_color"],
                "minutes": 0,
                "count": 0,
                "descriptions": []
            }
        segment_stats[seg_name]["minutes"] += session["duration_minutes"]
        segment_stats[seg_name]["count"] += 1
        if session["description"]:
            segment_stats[seg_name]["descriptions"].append(session["description"])
    
    return {
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 1),
        "total_pomodoros": total_pomodoros,
        "segments": list(segment_stats.values()),
        "sessions": sessions
    }


def get_weekly_stats() -> dict:
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    start_date = monday.strftime("%Y-%m-%d")
    end_date = sunday.strftime("%Y-%m-%d")
    
    sessions = get_sessions_by_date_range(start_date, end_date)
    
    total_minutes = sum(s["duration_minutes"] for s in sessions)
    
    segment_stats = {}
    for session in sessions:
        seg_name = session["segment_name"]
        if seg_name not in segment_stats:
            segment_stats[seg_name] = {
                "name": seg_name,
                "color": session["segment_color"],
                "minutes": 0,
                "count": 0
            }
        segment_stats[seg_name]["minutes"] += session["duration_minutes"]
        segment_stats[seg_name]["count"] += 1
    
    daily_stats = {}
    for session in sessions:
        day = session["completed_at"][:10]
        if day not in daily_stats:
            daily_stats[day] = {"minutes": 0, "count": 0}
        daily_stats[day]["minutes"] += session["duration_minutes"]
        daily_stats[day]["count"] += 1
    
    return {
        "week_start": start_date,
        "week_end": end_date,
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 1),
        "total_pomodoros": len(sessions),
        "segments": list(segment_stats.values()),
        "daily": daily_stats
    }


init_db()
