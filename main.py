import threading
import argparse
from dashboard import run_dashboard
from timer_widget import PomodoroTimer

def main():
    parser = argparse.ArgumentParser(description='Pomodoro Focus Tracker')
    parser.add_argument('--dashboard-only', action='store_true', help='Run only the dashboard')
    parser.add_argument('--timer-only', action='store_true', help='Run only the timer widget')
    parser.add_argument('--port', type=int, default=5050, help='Dashboard port (default: 5050)')
    args = parser.parse_args()
    
    if args.dashboard_only:
        run_dashboard(port=args.port)
    elif args.timer_only:
        app = PomodoroTimer()
        app.run()
    else:
        dashboard_thread = threading.Thread(
            target=run_dashboard,
            kwargs={'port': args.port},
            daemon=True
        )
        dashboard_thread.start()
        
        app = PomodoroTimer()
        app.run()


if __name__ == "__main__":
    main()
