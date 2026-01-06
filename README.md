# 🍅 Pomodoro Focus Tracker

A minimal, elegant floating timer widget for macOS that helps you track your laptop usage and productivity using the Pomodoro Technique.

## Why?

Track **actual laptop work time** across different activities - not your entire day, just the time you spend on your computer. Perfect for:
- Understanding where your laptop time goes
- Building focused work habits
- Analyzing productivity patterns
- Tracking deep work sessions

## What?

**Ultra-Minimal Floating Widget** (140x120px)
- Always-on-top timer that stays visible
- One-click start/pause/reset controls
- 5 fixed work segments with color coding
- Draggable, stays out of your way

**Analytics Dashboard** (http://localhost:5050)
- Day view: Sessions grouped by time (Morning/Afternoon/Evening/Midnight)
- Week view: Daily breakdown with segment distribution
- Month view: Heatmap calendar showing productivity patterns
- All stats: cycles completed, hours tracked, segment breakdown

## Features

### Timer Widget
- ⏱️ **25-minute Pomodoro cycles** with 5-minute breaks
- 🎨 **5 Color-coded segments**: Work, Solve, Build, Learn, Chill
- 🔝 **Always on top** - never loses focus
- 🖱️ **Draggable** - position anywhere on screen
- ⚫ **Pure dark mode** - minimal distraction
- 🔔 **Sound notifications** when cycles complete

### Dashboard Analytics
- 📊 **Time-based grouping**: Morning (6-12), Afternoon (12-6), Evening (6-12), Midnight (12-6)
- 📈 **Weekly trends**: See your productivity patterns
- 🗓️ **Monthly heatmap**: Visual representation of work intensity
- 🎯 **Segment breakdown**: Understand time distribution across activities

### 5 Fixed Segments
1. 🔴 **Work** - Office/Job work
2. 🟡 **Solve** - Problem solving (DSA, Math, System Design)
3. 🟢 **Build** - Side projects, building things
4. 🔵 **Learn** - Upskilling, reading, learning new concepts
5. 🟣 **Chill** - Netflix, YouTube, leisure time

## How to Use?

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/kevinAshah/pomodoro-tracker.git
cd pomodoro-tracker
```

2. **Create virtual environment** (Python 3.14+ recommended for Tkinter support)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Running the App

**Start both timer and dashboard:**
```bash
python main.py
```

**Timer only:**
```bash
python main.py --timer-only
```

**Dashboard only:**
```bash
python main.py --dashboard-only --port 5050
```

### Using the Timer

1. **Select your segment** from the dropdown (Work, Solve, Build, Learn, Chill)
2. **Click ▶** to start a 25-minute cycle
3. **Focus on your task** - timer stays on top
4. **When complete**, add a quick description of what you did
5. **Choose**: Take a 5-min break OR skip and continue

**Controls:**
- `▶/⏸` - Start/Pause timer
- `⏹` - Reset (doesn't save cycle)
- `●` (red) - Close app
- `●` (yellow) - Minimize (auto-restores after 3s)
- `📈` - Open dashboard

### Viewing Analytics

Open http://localhost:5050 in your browser or click the 📈 icon.

**Tabs:**
- **Day**: See today's sessions grouped by time of day
- **Week**: 7-day breakdown with daily stats
- **Month**: Calendar heatmap showing work patterns

## Technical Details

### Stack
- **Frontend**: Tkinter (Python native GUI)
- **Backend**: Flask (lightweight web server)
- **Database**: SQLite (local storage in `~/.pomodoro_tracker/`)
- **Platform**: macOS optimized (works on other platforms with minor adjustments)

### Data Storage
All data stored locally in: `~/.pomodoro_tracker/pomodoro.db`

**Tables:**
- `segments` - 5 fixed work categories
- `sessions` - Completed pomodoro cycles with timestamps and descriptions

### File Structure
```
pomodoro_tracker/
├── main.py           # Entry point
├── timer_widget.py   # Floating timer UI
├── dashboard.py      # Analytics web interface
├── database.py       # SQLite operations
├── requirements.txt  # Dependencies
└── README.md
```

## FAQ

**Q: Can I customize the 5 segments?**
A: The names are fixed (Work, Solve, Build, Learn, Chill) but you can edit `database.py` to change them. The limit of 5 is intentional to keep things simple.

**Q: Can I change the timer duration?**
A: Yes! Edit `timer_widget.py`:
```python
self.work_duration = 25 * 60  # Change 25 to your preferred minutes
self.break_duration = 5 * 60   # Change 5 to your preferred break time
```

**Q: Why does the widget stay on top even when I click other windows?**
A: This is intentional! It's a floating timer meant to always be visible. Use the minimize button (●) if you need to hide it temporarily.

**Q: Can I use this on Windows/Linux?**
A: Yes, but you'll need to ensure Tkinter is installed. The traffic light buttons and some macOS-specific features may look different.

**Q: Does this track time when I'm away from my laptop?**
A: No! This only tracks active Pomodoro cycles you manually start. It's for laptop usage tracking, not life tracking.

**Q: What happens if I reset the timer?**
A: The cycle is NOT saved. Only completed cycles (timer reaches 0:00) are recorded in the database.

**Q: Can I export my data?**
A: The SQLite database is at `~/.pomodoro_tracker/pomodoro.db`. You can query it directly or build an export feature.

## Requirements

- Python 3.10+ (3.14+ recommended for best Tkinter support on macOS)
- macOS (optimized for, but works on other platforms)
- Flask (installed via requirements.txt)

## License

MIT License - feel free to modify and use as you wish!

## Contributing

This is a personal productivity tool, but suggestions and improvements are welcome! Open an issue or submit a PR.

---

**Built with focus. Track with intention. Work with purpose.** 🍅
