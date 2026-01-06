import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime
import platform
import subprocess
from database import get_segments, save_session, get_today_stats


class PomodoroTimer:
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    BREAK = "break"
    
    WIDGET_WIDTH = 140
    WIDGET_HEIGHT = 120
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pomodoro")
        
        self.work_duration = 25 * 60  
        self.break_duration = 5 * 60  
        self.time_remaining = self.work_duration
        self.state = self.IDLE
        self.session_start_time = None
        
        # Load 5 fixed segments
        self.segments = get_segments()
        self.current_segment_idx = 0
        
        self._setup_window()
        self._create_widgets()
        self._position_window()
        
        self.timer_thread = None
        self.running = True
        
        # Ensure widget stays on top periodically
        self._keep_on_top()
        
    def _setup_window(self):
        """Configure window properties for floating behavior."""
        # Remove window decorations to create custom title bar
        self.root.overrideredirect(True)
        
        # Always on top - CRITICAL for floating widget
        self.root.attributes('-topmost', True)
        
        # Prevent window from losing focus (stays on top always)
        self.root.lift()
        self.root.attributes('-topmost', 1)
        
        # Transparency
        self.root.attributes('-alpha', 0.96)
        
        # Pure black background
        self.root.configure(bg='#000000')
        
        # Fixed size
        self.root.geometry(f"{self.WIDGET_WIDTH}x{self.WIDGET_HEIGHT}")
        self.root.resizable(False, False)
        
        # Make window draggable
        self.root.bind('<Button-1>', self._start_drag)
        self.root.bind('<B1-Motion>', self._drag)
        
        # Ensure it stays on top even after other windows are clicked
        self.root.bind('<FocusOut>', lambda e: self.root.lift())
        
    def _position_window(self):
        """Position window at bottom-right corner."""
        self.root.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Position at bottom-right with padding
        x = screen_width - self.WIDGET_WIDTH - 20
        y = screen_height - self.WIDGET_HEIGHT - 80
        
        self.root.geometry(f"{self.WIDGET_WIDTH}x{self.WIDGET_HEIGHT}+{x}+{y}")
        
    def _create_widgets(self):
        """Create the ultra-minimal UI elements."""
        # Main container
        self.main_frame = tk.Frame(self.root, bg='#000000')
        self.main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Custom title bar with traffic lights
        title_bar = tk.Frame(self.main_frame, bg='#000000', height=18)
        title_bar.pack(fill='x', pady=(0, 5))
        title_bar.pack_propagate(False)
        
        # Traffic lights (left side)
        traffic_frame = tk.Frame(title_bar, bg='#000000')
        traffic_frame.pack(side='left')
        
        # Close button (red)
        close_btn = tk.Button(
            traffic_frame,
            text="●",
            command=self._quit,
            font=('Arial', 9),
            bg='#000000',
            fg='#ff5f56',
            activebackground='#000000',
            activeforeground='#ff5f56',
            bd=0,
            cursor='hand2',
            padx=0,
            pady=0,
            highlightthickness=0,
            relief='flat'
        )
        close_btn.pack(side='left', padx=1)
        
        # Minimize button (yellow)
        minimize_btn = tk.Button(
            traffic_frame,
            text="●",
            command=self._minimize,
            font=('Arial', 9),
            bg='#000000',
            fg='#ffbd2e',
            activebackground='#000000',
            activeforeground='#ffbd2e',
            bd=0,
            cursor='hand2',
            padx=0,
            pady=0,
            highlightthickness=0,
            relief='flat'
        )
        minimize_btn.pack(side='left', padx=1)
        
        # Timer section with controls
        timer_frame = tk.Frame(self.main_frame, bg='#000000')
        timer_frame.pack(fill='x', pady=(0, 8))
        
        # Timer display (left side)
        self.time_label = tk.Label(
            timer_frame,
            text="25:00",
            font=('SF Mono', 28, 'bold'),
            fg='#ffffff',
            bg='#000000'
        )
        self.time_label.pack(side='left')
        
        # Control buttons (right side, stacked)
        controls_frame = tk.Frame(timer_frame, bg='#000000')
        controls_frame.pack(side='right', padx=(5, 0))
        
        btn_style = {
            'font': ('SF Mono', 11),
            'bg': '#1a1a1a',
            'fg': '#ffffff',
            'activebackground': '#2a2a2a',
            'activeforeground': '#ffffff',
            'bd': 0,
            'width': 2,
            'height': 1,
            'cursor': 'hand2',
            'highlightthickness': 0,
            'relief': 'flat'
        }
        
        # Play/Pause button (top)
        self.play_btn = tk.Button(controls_frame, text="▶", command=self._toggle_timer, **btn_style)
        self.play_btn.pack(pady=(0, 2))
        
        # Reset button (bottom)
        self.reset_btn = tk.Button(controls_frame, text="⏹", command=self._reset_timer, **btn_style)
        self.reset_btn.pack()
        
        # Segment selector with dashboard icon (no label, just color + dropdown + icon)
        seg_frame = tk.Frame(self.main_frame, bg='#000000')
        seg_frame.pack(fill='x', pady=(0, 3))
        
        # Color indicator
        self.color_canvas = tk.Canvas(
            seg_frame,
            width=10,
            height=10,
            bg='#000000',
            highlightthickness=0
        )
        self.color_canvas.pack(side='left', padx=(0, 5))
        self.color_dot = self.color_canvas.create_oval(
            1, 1, 9, 9, 
            fill=self.segments[0]['color'] if self.segments else '#666666'
        )
        
        # Segment dropdown
        self.segment_var = tk.StringVar(value=self.segments[0]['name'] if self.segments else "")
        
        # Style the combobox for pure dark mode
        style = ttk.Style()
        style.theme_use('default')
        
        # Configure combobox colors
        style.configure(
            'Dark.TCombobox',
            fieldbackground='#1a1a1a',
            background='#1a1a1a',
            foreground='#ffffff',
            arrowcolor='#ffffff',
            borderwidth=0,
            relief='flat'
        )
        
        # Map for dropdown list colors
        style.map('Dark.TCombobox',
            fieldbackground=[('readonly', '#1a1a1a')],
            selectbackground=[('readonly', '#2a2a2a')],
            selectforeground=[('readonly', '#ffffff')]
        )
        
        self.segment_dropdown = ttk.Combobox(
            seg_frame,
            textvariable=self.segment_var,
            values=[s['name'] for s in self.segments],
            state='readonly',
            width=8,
            style='Dark.TCombobox',
            font=('SF Pro', 10)
        )
        self.segment_dropdown.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.segment_dropdown.bind('<<ComboboxSelected>>', self._on_segment_change)
        
        # Dashboard button (right side of segment dropdown, smaller)
        self.dash_btn = tk.Button(
            seg_frame,
            text="📈",
            command=self._open_dashboard,
            font=('SF Mono', 10),
            bg='#000000',
            fg='#ffffff',
            activebackground='#000000',
            activeforeground='#888888',
            bd=0,
            cursor='hand2',
            padx=0,
            pady=0,
            highlightthickness=0,
            relief='flat'
        )
        self.dash_btn.pack(side='right')
        
    def _on_segment_change(self, event=None):
        """Handle segment selection change."""
        selected = self.segment_var.get()
        for i, seg in enumerate(self.segments):
            if seg['name'] == selected:
                self.current_segment_idx = i
                # Update color indicator
                self.color_canvas.itemconfig(self.color_dot, fill=seg['color'])
                break
                
    def _toggle_timer(self):
        """Toggle timer start/pause."""
        if self.state == self.IDLE:
            self._start_timer()
        elif self.state == self.RUNNING:
            self._pause_timer()
        elif self.state == self.PAUSED:
            self._start_timer()
        elif self.state == self.BREAK:
            self._pause_timer()
            
    def _start_timer(self):
        """Start or resume the timer."""
        if self.state == self.IDLE:
            self.session_start_time = datetime.now()
            self.time_remaining = self.work_duration
        elif self.state == self.BREAK:
            # Resuming break
            pass
            
        self.state = self.RUNNING if self.state != self.BREAK else self.BREAK
        
        # Update button to pause icon
        self.play_btn.config(text="⏸")
        
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()
            
    def _pause_timer(self):
        """Pause the timer."""
        if self.state == self.RUNNING or self.state == self.BREAK:
            self.state = self.PAUSED
            self.play_btn.config(text="▶")
            
    def _reset_timer(self):
        """Reset the timer (does NOT save the cycle)."""
        self.state = self.IDLE
        self.time_remaining = self.work_duration
        self.session_start_time = None
        self._update_time_display()
        self.play_btn.config(text="▶")
        
    def _timer_loop(self):
        """Background timer loop."""
        while self.running:
            if self.state == self.RUNNING:
                if self.time_remaining > 0:
                    self.time_remaining -= 1
                    self.root.after(0, self._update_time_display)
                else:
                    self.root.after(0, self._timer_complete)
                    return
            elif self.state == self.BREAK:
                if self.time_remaining > 0:
                    self.time_remaining -= 1
                    self.root.after(0, self._update_time_display)
                else:
                    self.root.after(0, self._break_complete)
                    return
            time.sleep(1)
            
    def _timer_complete(self):
        """Handle work timer completion."""
        self.state = self.IDLE
        self._play_notification_sound()
        self._show_completion_dialog()
        
    def _break_complete(self):
        """Handle break timer completion."""
        self.state = self.IDLE
        self._play_notification_sound()
        self._notify("Break's over!", "Ready for another pomodoro?")
        self._reset_timer()
        
    def _show_completion_dialog(self):
        """Show minimal dialog to log the completed session."""
        dialog = tk.Toplevel(self.root)
        dialog.title("🍅 Pomodoro Complete!")
        dialog.configure(bg='#0a0a0a')
        dialog.attributes('-topmost', True)
        dialog.geometry("380x180")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 380) // 2
        y = (dialog.winfo_screenheight() - 180) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Title
        tk.Label(
            dialog,
            text="🍅 Great work! What did you do?",
            font=('SF Pro', 13, 'bold'),
            fg='#ffffff',
            bg='#0a0a0a'
        ).pack(pady=(15, 5))
        
        # Segment display with color
        segment = self.segments[self.current_segment_idx]
        seg_frame = tk.Frame(dialog, bg='#0a0a0a')
        seg_frame.pack(pady=5)
        
        color_canvas = tk.Canvas(seg_frame, width=12, height=12, bg='#0a0a0a', highlightthickness=0)
        color_canvas.pack(side='left', padx=(0, 5))
        color_canvas.create_oval(2, 2, 10, 10, fill=segment['color'])
        
        tk.Label(
            seg_frame,
            text=segment['name'],
            font=('SF Pro', 11),
            fg='#888888',
            bg='#0a0a0a'
        ).pack(side='left')
        
        # Description entry (1-line)
        desc_entry = tk.Entry(
            dialog,
            font=('SF Pro', 11),
            bg='#1a1a1a',
            fg='#ffffff',
            insertbackground='#ffffff',
            bd=0,
            width=40
        )
        desc_entry.pack(pady=10, padx=20, ipady=6)
        desc_entry.focus_set()
        desc_entry.insert(0, "Quick description...")
        desc_entry.bind('<FocusIn>', lambda e: desc_entry.delete(0, tk.END) if desc_entry.get() == "Quick description..." else None)
        
        def save_and_break():
            """Save session and start break."""
            description = desc_entry.get().strip()
            if description == "Quick description...":
                description = ""
            if self.session_start_time:
                save_session(
                    segment_id=segment['id'],
                    description=description or "No description",
                    duration_minutes=25,
                    started_at=self.session_start_time
                )
            dialog.destroy()
            self._start_break()
            
        def save_and_skip():
            """Save session and skip break."""
            description = desc_entry.get().strip()
            if description == "Quick description...":
                description = ""
            if self.session_start_time:
                save_session(
                    segment_id=segment['id'],
                    description=description or "No description",
                    duration_minutes=25,
                    started_at=self.session_start_time
                )
            dialog.destroy()
            self._reset_timer()
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='#0a0a0a')
        btn_frame.pack(pady=15)
        
        tk.Button(
            btn_frame,
            text="Save & Break (5 min)",
            command=save_and_break,
            font=('SF Pro', 10),
            bg='#2ecc71',
            fg='#ffffff',
            activebackground='#27ae60',
            bd=0,
            padx=15,
            pady=6,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="Skip Break",
            command=save_and_skip,
            font=('SF Pro', 10),
            bg='#2a2a2a',
            fg='#ffffff',
            activebackground='#3a3a3a',
            bd=0,
            padx=15,
            pady=6,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Bind Enter key to save & break
        desc_entry.bind('<Return>', lambda e: save_and_break())
        
    def _start_break(self):
        """Start the break timer."""
        self.time_remaining = self.break_duration
        self.state = self.BREAK
        self._update_time_display()
        self.play_btn.config(text="⏸")
        
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
        
    def _update_time_display(self):
        """Update the timer display."""
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        
    def _play_notification_sound(self):
        """Play notification sound (macOS)."""
        if platform.system() == 'Darwin':
            subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], capture_output=True)
        else:
            self.root.bell()
            
    def _notify(self, title: str, message: str):
        """Show system notification (macOS)."""
        if platform.system() == 'Darwin':
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], capture_output=True)
            
    def _open_dashboard(self):
        """Open the analytics dashboard in browser."""
        import webbrowser
        webbrowser.open('http://localhost:5050')
    
    def _start_drag(self, event):
        """Start window drag."""
        # Only allow drag if not clicking on a button
        widget = event.widget
        if isinstance(widget, tk.Button) or isinstance(widget, ttk.Combobox):
            return
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def _drag(self, event):
        """Handle window drag."""
        if hasattr(self, '_drag_start_x'):
            x = self.root.winfo_x() + event.x - self._drag_start_x
            y = self.root.winfo_y() + event.y - self._drag_start_y
            self.root.geometry(f"+{x}+{y}")
    
    def _minimize(self):
        """Minimize the window (hide it temporarily)."""
        # With overrideredirect(True), standard minimize doesn't work
        # So we'll hide the window instead
        self.root.withdraw()
        
        # Create a small restore mechanism - window will auto-restore after 3 seconds
        # Or you can click the dock icon to restore
        def restore():
            self.root.deiconify()
            self.root.lift()
        
        # Auto-restore after 3 seconds (you can adjust this)
        self.root.after(3000, restore)
    
    def _keep_on_top(self):
        """Periodically ensure window stays on top."""
        self.root.lift()
        self.root.attributes('-topmost', True)
        # Check every 500ms
        self.root.after(500, self._keep_on_top)
    
    def _quit(self):
        """Close the application."""
        self.running = False
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """Start the application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = PomodoroTimer()
    app.run()
