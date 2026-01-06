from flask import Flask, render_template_string, jsonify
from database import (
    get_today_stats, 
    get_weekly_stats, 
    get_today_sessions_by_time_segment,
    get_sessions_by_date_range
)
from datetime import datetime, timedelta

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍅 Pomodoro Analytics</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
        }
        
        header h1 {
            font-size: 2.2rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        header p {
            color: #888;
            font-size: 0.95rem;
        }
        
        /* Tabs */
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 2px solid #222;
            padding-bottom: 0;
        }
        
        .tab {
            padding: 12px 24px;
            background: transparent;
            border: none;
            color: #888;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.05);
        }
        
        .tab.active {
            color: #fff;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Summary Stats */
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        
        .stat-card .value {
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }
        
        .stat-card .label {
            color: #888;
            font-size: 0.85rem;
        }
        
        /* Time Segments */
        .time-segments {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .time-segment {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 20px;
        }
        
        .time-segment h3 {
            font-size: 1.1rem;
            margin-bottom: 8px;
            color: #fff;
        }
        
        .time-segment .segment-stats {
            color: #888;
            font-size: 0.85rem;
            margin-bottom: 15px;
        }
        
        .session-item {
            background: #0f0f0f;
            border-left: 3px solid;
            padding: 10px 12px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        .session-item .time {
            color: #888;
            font-size: 0.8rem;
            margin-bottom: 3px;
        }
        
        .session-item .segment-name {
            font-weight: 600;
            margin-bottom: 2px;
        }
        
        .session-item .description {
            color: #aaa;
            font-size: 0.85rem;
        }
        
        .empty-state {
            text-align: center;
            color: #666;
            padding: 40px 20px;
            font-size: 0.9rem;
        }
        
        /* Weekly View */
        .daily-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .day-card {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
        }
        
        .day-card .day-name {
            color: #888;
            font-size: 0.8rem;
            margin-bottom: 5px;
        }
        
        .day-card .day-date {
            color: #fff;
            font-size: 0.9rem;
            margin-bottom: 10px;
        }
        
        .day-card .day-count {
            font-size: 1.8rem;
            font-weight: 700;
            color: #667eea;
        }
        
        .day-card .day-hours {
            color: #888;
            font-size: 0.75rem;
            margin-top: 5px;
        }
        
        /* Segment Breakdown */
        .segment-breakdown {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .segment-breakdown h3 {
            font-size: 1.1rem;
            margin-bottom: 15px;
        }
        
        .segment-row {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .segment-row .color-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        
        .segment-row .name {
            flex: 1;
            font-size: 0.9rem;
        }
        
        .segment-row .count {
            font-weight: 600;
            margin-right: 10px;
        }
        
        .segment-row .percentage {
            color: #888;
            font-size: 0.85rem;
        }
        
        /* Month View - Heatmap */
        .heatmap {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .heatmap h3 {
            font-size: 1.1rem;
            margin-bottom: 15px;
        }
        
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 8px;
        }
        
        .calendar-day {
            aspect-ratio: 1;
            background: #0f0f0f;
            border-radius: 6px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            border: 1px solid #222;
        }
        
        .calendar-day .date {
            color: #888;
            font-size: 0.75rem;
        }
        
        .calendar-day .count {
            font-weight: 600;
            margin-top: 2px;
        }
        
        .calendar-day.intensity-0 { background: #0f0f0f; }
        .calendar-day.intensity-1 { background: rgba(102, 126, 234, 0.2); }
        .calendar-day.intensity-2 { background: rgba(102, 126, 234, 0.4); }
        .calendar-day.intensity-3 { background: rgba(102, 126, 234, 0.6); }
        .calendar-day.intensity-4 { background: rgba(102, 126, 234, 0.8); }
        .calendar-day.intensity-5 { background: rgba(102, 126, 234, 1); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🍅 Pomodoro Analytics</h1>
            <p>Track your laptop usage and productivity</p>
        </header>
        
        <!-- Tabs -->
        <div class="tabs">
            <button class="tab active" onclick="switchTab('day')">Day</button>
            <button class="tab" onclick="switchTab('week')">Week</button>
            <button class="tab" onclick="switchTab('month')">Month</button>
        </div>
        
        <!-- Day View -->
        <div id="day-tab" class="tab-content active">
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="value" id="today-cycles">0</div>
                    <div class="label">Cycles Today</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="today-hours">0.0</div>
                    <div class="label">Hours</div>
                </div>
            </div>
            
            <div class="time-segments" id="time-segments">
                <!-- Populated by JS -->
            </div>
        </div>
        
        <!-- Week View -->
        <div id="week-tab" class="tab-content">
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="value" id="week-cycles">0</div>
                    <div class="label">Cycles This Week</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="week-hours">0.0</div>
                    <div class="label">Hours</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="week-avg">0</div>
                    <div class="label">Avg/Day</div>
                </div>
            </div>
            
            <div class="daily-grid" id="daily-grid">
                <!-- Populated by JS -->
            </div>
            
            <div class="segment-breakdown">
                <h3>Segment Breakdown</h3>
                <div id="week-segments">
                    <!-- Populated by JS -->
                </div>
            </div>
        </div>
        
        <!-- Month View -->
        <div id="month-tab" class="tab-content">
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="value" id="month-cycles">0</div>
                    <div class="label">Cycles This Month</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="month-hours">0.0</div>
                    <div class="label">Hours</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="month-best">0</div>
                    <div class="label">Best Day</div>
                </div>
            </div>
            
            <div class="heatmap">
                <h3 id="month-title">January 2025</h3>
                <div class="calendar-grid" id="calendar-grid">
                    <!-- Populated by JS -->
                </div>
            </div>
            
            <div class="segment-breakdown">
                <h3>Segment Breakdown</h3>
                <div id="month-segments">
                    <!-- Populated by JS -->
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching
        function switchTab(tab) {
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(tab + '-tab').classList.add('active');
            
            // Load data for the tab
            if (tab === 'day') loadDayData();
            else if (tab === 'week') loadWeekData();
            else if (tab === 'month') loadMonthData();
        }
        
        // Load day view data
        async function loadDayData() {
            const response = await fetch('/api/today');
            const data = await response.json();
            
            document.getElementById('today-cycles').textContent = data.total_pomodoros;
            document.getElementById('today-hours').textContent = data.total_hours;
            
            // Render time segments
            const container = document.getElementById('time-segments');
            container.innerHTML = '';
            
            const segments = ['morning', 'afternoon', 'evening', 'midnight'];
            const labels = {
                'morning': 'Morning (6 AM - 12 PM)',
                'afternoon': 'Afternoon (12 PM - 6 PM)',
                'evening': 'Evening (6 PM - 12 AM)',
                'midnight': 'Midnight (12 AM - 6 AM)'
            };
            
            segments.forEach(seg => {
                const segData = data.time_segments[seg];
                const div = document.createElement('div');
                div.className = 'time-segment';
                
                let sessionsHtml = '';
                if (segData.sessions.length === 0) {
                    sessionsHtml = '<div class="empty-state">No sessions yet</div>';
                } else {
                    segData.sessions.forEach(session => {
                        const startTime = new Date(session.started_at).toLocaleTimeString('en-US', {
                            hour: 'numeric',
                            minute: '2-digit',
                            hour12: true
                        });
                        const endTime = new Date(new Date(session.started_at).getTime() + session.duration_minutes * 60000).toLocaleTimeString('en-US', {
                            hour: 'numeric',
                            minute: '2-digit',
                            hour12: true
                        });
                        
                        sessionsHtml += `
                            <div class="session-item" style="border-left-color: ${session.segment_color}">
                                <div class="time">${startTime} - ${endTime}</div>
                                <div class="segment-name">${session.segment_name}</div>
                                <div class="description">${session.description}</div>
                            </div>
                        `;
                    });
                }
                
                div.innerHTML = `
                    <h3>${labels[seg]}</h3>
                    <div class="segment-stats">${segData.count} cycles • ${(segData.minutes / 60).toFixed(1)} hrs</div>
                    ${sessionsHtml}
                `;
                
                container.appendChild(div);
            });
        }
        
        // Load week view data
        async function loadWeekData() {
            const response = await fetch('/api/week');
            const data = await response.json();
            
            document.getElementById('week-cycles').textContent = data.total_pomodoros;
            document.getElementById('week-hours').textContent = data.total_hours;
            document.getElementById('week-avg').textContent = Math.round(data.total_pomodoros / 7);
            
            // Render daily grid
            const container = document.getElementById('daily-grid');
            container.innerHTML = '';
            
            const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            const startDate = new Date(data.week_start);
            
            for (let i = 0; i < 7; i++) {
                const date = new Date(startDate);
                date.setDate(startDate.getDate() + i);
                const dateStr = date.toISOString().split('T')[0];
                const dayData = data.daily[dateStr] || { count: 0, minutes: 0 };
                
                const div = document.createElement('div');
                div.className = 'day-card';
                div.innerHTML = `
                    <div class="day-name">${days[i]}</div>
                    <div class="day-date">${date.getDate()}</div>
                    <div class="day-count">${dayData.count}</div>
                    <div class="day-hours">${(dayData.minutes / 60).toFixed(1)} hrs</div>
                `;
                container.appendChild(div);
            }
            
            // Render segment breakdown
            const segContainer = document.getElementById('week-segments');
            segContainer.innerHTML = '';
            
            data.segments.forEach(seg => {
                const percentage = Math.round((seg.count / data.total_pomodoros) * 100) || 0;
                const div = document.createElement('div');
                div.className = 'segment-row';
                div.innerHTML = `
                    <div class="color-dot" style="background: ${seg.color}"></div>
                    <div class="name">${seg.name}</div>
                    <div class="count">${seg.count} cycles</div>
                    <div class="percentage">${percentage}%</div>
                `;
                segContainer.appendChild(div);
            });
        }
        
        // Load month view data
        async function loadMonthData() {
            const response = await fetch('/api/month');
            const data = await response.json();
            
            document.getElementById('month-cycles').textContent = data.total_pomodoros;
            document.getElementById('month-hours').textContent = data.total_hours;
            document.getElementById('month-best').textContent = data.best_day_count;
            document.getElementById('month-title').textContent = data.month_name;
            
            // Render calendar heatmap
            const container = document.getElementById('calendar-grid');
            container.innerHTML = '';
            
            const firstDay = new Date(data.month_start);
            const lastDay = new Date(data.month_end);
            const startDayOfWeek = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1; // Monday = 0
            
            // Add empty cells for days before month starts
            for (let i = 0; i < startDayOfWeek; i++) {
                const div = document.createElement('div');
                div.className = 'calendar-day';
                container.appendChild(div);
            }
            
            // Add days of month
            const currentDate = new Date(firstDay);
            while (currentDate <= lastDay) {
                const dateStr = currentDate.toISOString().split('T')[0];
                const dayData = data.daily[dateStr] || { count: 0 };
                
                // Calculate intensity (0-5 based on count)
                let intensity = 0;
                if (dayData.count > 0) intensity = 1;
                if (dayData.count >= 3) intensity = 2;
                if (dayData.count >= 5) intensity = 3;
                if (dayData.count >= 7) intensity = 4;
                if (dayData.count >= 10) intensity = 5;
                
                const div = document.createElement('div');
                div.className = `calendar-day intensity-${intensity}`;
                div.innerHTML = `
                    <div class="date">${currentDate.getDate()}</div>
                    <div class="count">${dayData.count}</div>
                `;
                container.appendChild(div);
                
                currentDate.setDate(currentDate.getDate() + 1);
            }
            
            // Render segment breakdown
            const segContainer = document.getElementById('month-segments');
            segContainer.innerHTML = '';
            
            data.segments.forEach(seg => {
                const percentage = Math.round((seg.count / data.total_pomodoros) * 100) || 0;
                const div = document.createElement('div');
                div.className = 'segment-row';
                div.innerHTML = `
                    <div class="color-dot" style="background: ${seg.color}"></div>
                    <div class="name">${seg.name}</div>
                    <div class="count">${seg.count} cycles</div>
                    <div class="percentage">${percentage}%</div>
                `;
                segContainer.appendChild(div);
            });
        }
        
        // Initial load
        loadDayData();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            const activeTab = document.querySelector('.tab.active').textContent.toLowerCase();
            if (activeTab === 'day') loadDayData();
            else if (activeTab === 'week') loadWeekData();
            else if (activeTab === 'month') loadMonthData();
        }, 30000);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/today')
def api_today():
    stats = get_today_stats()
    time_segments = get_today_sessions_by_time_segment()
    
    return jsonify({
        'total_pomodoros': stats['total_pomodoros'],
        'total_hours': stats['total_hours'],
        'time_segments': time_segments
    })


@app.route('/api/week')
def api_week():
    stats = get_weekly_stats()
    return jsonify(stats)


@app.route('/api/month')
def api_month():
    today = datetime.now()
    month_start = today.replace(day=1)
    
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    start_date = month_start.strftime("%Y-%m-%d")
    end_date = month_end.strftime("%Y-%m-%d")
    
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
    
    best_day_count = max([d["count"] for d in daily_stats.values()]) if daily_stats else 0
    
    return jsonify({
        "month_name": today.strftime("%B %Y"),
        "month_start": start_date,
        "month_end": end_date,
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 1),
        "total_pomodoros": len(sessions),
        "segments": list(segment_stats.values()),
        "daily": daily_stats,
        "best_day_count": best_day_count
    })


def run_dashboard(port: int = 5050):
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == "__main__":
    run_dashboard()
