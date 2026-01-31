"""
Pomodoro Timer Widget - Clean Dark UI
Fixed: Using Label widgets for buttons (reliable on macOS)
"""

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
    
    # Compact square dimensions
    WIDGET_WIDTH = 120
    WIDGET_HEIGHT = 85
    
    # Colors
    BG = '#0d0d0d'
    BG_LIGHT = '#1a1a1a'
    BG_HOVER = '#2a2a2a'
    FG = '#ffffff'
    FG_DIM = '#888888'
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pomodoro")
        
        self.work_duration = 25 * 60  
        self.break_duration = 5 * 60  
        self.time_remaining = self.work_duration
        self.state = self.IDLE
        self.session_start_time = None
        
        self.segments = get_segments()
        self.current_segment_idx = 0
        
        self._setup_window()
        self._create_widgets()
        self._position_window()
        
        self.timer_thread = None
        self.running = True
        self._keep_on_top()
        
    def _setup_window(self):
        """Configure window properties."""
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.lift()
        self.root.attributes('-alpha', 0.96)
        self.root.configure(bg=self.BG)
        self.root.geometry(f"{self.WIDGET_WIDTH}x{self.WIDGET_HEIGHT}")
        self.root.resizable(False, False)
        
        self.root.bind('<Button-1>', self._start_drag)
        self.root.bind('<B1-Motion>', self._drag)
        self.root.bind('<FocusOut>', lambda e: self.root.lift())
        
    def _position_window(self):
        """Position at bottom-right corner."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - self.WIDGET_WIDTH - 20
        y = screen_height - self.WIDGET_HEIGHT - 80
        self.root.geometry(f"{self.WIDGET_WIDTH}x{self.WIDGET_HEIGHT}+{x}+{y}")
    
    def _make_label_button(self, parent, text, command, width=3, bg=None, fg=None, font=None):
        """Create a Label that acts as a button (works on macOS without white bg)."""
        bg = bg or self.BG_LIGHT
        fg = fg or self.FG
        font = font or ('SF Mono', 12)
        
        label = tk.Label(
            parent,
            text=text,
            font=font,
            fg=fg,
            bg=bg,
            width=width,
            cursor='hand2'
        )
        
        # Store original bg for hover
        label._original_bg = bg
        
        # Hover effects
        def on_enter(e):
            label.config(bg=self.BG_HOVER)
        def on_leave(e):
            label.config(bg=label._original_bg)
        def on_click(e):
            command()
            
        label.bind('<Enter>', on_enter)
        label.bind('<Leave>', on_leave)
        label.bind('<Button-1>', on_click)
        
        return label
        
    def _create_widgets(self):
        """Create the UI - 2 column layout matching wireframe."""
        # Main container - 2 columns side by side
        self.main_frame = tk.Frame(self.root, bg=self.BG)
        self.main_frame.pack(fill='both', expand=True, padx=6, pady=4)
        
        # === LEFT COLUMN: Traffic lights, Timer, Segment ===
        left_col = tk.Frame(self.main_frame, bg=self.BG)
        left_col.pack(side='left', fill='both', expand=True)
        
        # Traffic lights (top of left column)
        traffic_frame = tk.Frame(left_col, bg=self.BG)
        traffic_frame.pack(anchor='w', pady=(0, 0))
        
        # Close button (red circle)
        self.close_canvas = tk.Canvas(traffic_frame, width=14, height=14, bg=self.BG, highlightthickness=0)
        self.close_canvas.pack(side='left', padx=(0, 3))
        self.close_dot = self.close_canvas.create_oval(2, 2, 12, 12, fill='#ff5f56', outline='')
        self.close_canvas.bind('<Button-1>', lambda e: self._quit())
        self.close_canvas.bind('<Enter>', lambda e: self.close_canvas.itemconfig(self.close_dot, fill='#ff3b30'))
        self.close_canvas.bind('<Leave>', lambda e: self.close_canvas.itemconfig(self.close_dot, fill='#ff5f56'))
        self.close_canvas.config(cursor='hand2')
        
        # Minimize button (yellow circle)
        self.min_canvas = tk.Canvas(traffic_frame, width=14, height=14, bg=self.BG, highlightthickness=0)
        self.min_canvas.pack(side='left')
        self.min_dot = self.min_canvas.create_oval(2, 2, 12, 12, fill='#ffbd2e', outline='')
        self.min_canvas.bind('<Button-1>', lambda e: self._minimize())
        self.min_canvas.bind('<Enter>', lambda e: self.min_canvas.itemconfig(self.min_dot, fill='#ff9500'))
        self.min_canvas.bind('<Leave>', lambda e: self.min_canvas.itemconfig(self.min_dot, fill='#ffbd2e'))
        self.min_canvas.config(cursor='hand2')
        
        # Timer display (middle of left column)
        self.time_label = tk.Label(
            left_col,
            text="25:00",
            font=('SF Mono', 26, 'bold'),
            fg=self.FG,
            bg=self.BG
        )
        self.time_label.pack(anchor='w', pady=(2, 2))
        
        # Segment row (bottom of left column)
        segment_frame = tk.Frame(left_col, bg=self.BG)
        segment_frame.pack(anchor='w', fill='x')
        
        # Color indicator
        self.color_canvas = tk.Canvas(segment_frame, width=10, height=10, bg=self.BG, highlightthickness=0)
        self.color_canvas.pack(side='left', padx=(0, 4))
        initial_color = self.segments[0]['color'] if self.segments else '#666666'
        self.color_dot = self.color_canvas.create_oval(1, 1, 9, 9, fill=initial_color, outline='')
        
        # Segment dropdown
        self.segment_var = tk.StringVar(value=self.segments[0]['name'] if self.segments else "")
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Dark.TCombobox',
            fieldbackground=self.BG_LIGHT,
            background=self.BG_LIGHT,
            foreground=self.FG,
            arrowcolor='#666666',
            borderwidth=0
        )
        style.map('Dark.TCombobox',
            fieldbackground=[('readonly', self.BG_LIGHT)],
            selectbackground=[('readonly', self.BG_HOVER)],
            selectforeground=[('readonly', self.FG)]
        )
        
        self.root.option_add('*TCombobox*Listbox.background', self.BG_LIGHT)
        self.root.option_add('*TCombobox*Listbox.foreground', self.FG)
        self.root.option_add('*TCombobox*Listbox.selectBackground', '#333333')
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.FG)
        
        self.segment_dropdown = ttk.Combobox(
            segment_frame,
            textvariable=self.segment_var,
            values=[s['name'] for s in self.segments],
            state='readonly',
            width=7,
            style='Dark.TCombobox',
            font=('SF Pro', 10)
        )
        self.segment_dropdown.pack(side='left')
        self.segment_dropdown.bind('<<ComboboxSelected>>', self._on_segment_change)
        
        # === RIGHT COLUMN: 3 buttons stacked vertically ===
        right_col = tk.Frame(self.main_frame, bg=self.BG)
        right_col.pack(side='right', fill='y', padx=(4, 0))
        
        # Play/Pause button (top)
        self.play_btn = self._make_label_button(
            right_col, 
            text="▶", 
            command=self._toggle_timer,
            width=2
        )
        self.play_btn.pack(pady=(0, 3))
        
        # Reset/Stop button (middle)
        self.reset_btn = self._make_label_button(
            right_col,
            text="⏹",
            command=self._reset_timer,
            width=2
        )
        self.reset_btn.pack(pady=(0, 3))
        
        # Dashboard button (bottom)
        self.dash_btn = self._make_label_button(
            right_col,
            text="📈",
            command=self._open_dashboard,
            width=2,
            font=('', 11)
        )
        self.dash_btn.pack()
        
    def _on_segment_change(self, event=None):
        """Handle segment change."""
        selected = self.segment_var.get()
        for i, seg in enumerate(self.segments):
            if seg['name'] == selected:
                self.current_segment_idx = i
                self.color_canvas.itemconfig(self.color_dot, fill=seg['color'])
                break
                
    def _toggle_timer(self):
        """Toggle start/pause."""
        if self.state == self.IDLE:
            self._start_timer()
        elif self.state == self.RUNNING:
            self._pause_timer()
        elif self.state == self.PAUSED:
            self._resume_timer()
        elif self.state == self.BREAK:
            self._pause_timer()
            
    def _start_timer(self):
        """Start timer."""
        # Stop any existing timer loop first
        self.state = self.IDLE
        time.sleep(0.1)  # Give existing thread time to exit
        
        self.session_start_time = datetime.now()
        self.time_remaining = self.work_duration
        self.state = self.RUNNING
        self.play_btn.config(text="⏸")
        self.time_label.config(fg=self.FG)  # White for work
        
        # Only start new thread if none is running
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()
        
    def _pause_timer(self):
        """Pause timer."""
        self.state = self.PAUSED
        self.play_btn.config(text="▶")
        
    def _resume_timer(self):
        """Resume timer."""
        self.state = self.RUNNING
        self.play_btn.config(text="⏸")
        
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()
        
    def _reset_timer(self):
        """Reset timer."""
        self.state = self.IDLE
        self.time_remaining = self.work_duration
        self.session_start_time = None
        self._update_time_display()
        self.play_btn.config(text="▶")
        self.time_label.config(fg=self.FG)
        
    def _timer_loop(self):
        """Background timer."""
        while self.running:
            if self.state == self.RUNNING or self.state == self.BREAK:
                if self.time_remaining > 0:
                    self.time_remaining -= 1
                    self.root.after(0, self._update_time_display)
                else:
                    if self.state == self.RUNNING:
                        self.root.after(0, self._timer_complete)
                    else:
                        self.root.after(0, self._break_complete)
                    return
                time.sleep(1)
            elif self.state == self.IDLE or self.state == self.PAUSED:
                # Exit thread when idle or paused - will be restarted when needed
                return
            else:
                time.sleep(0.1)
            
    def _timer_complete(self):
        """Work timer done."""
        self.state = self.IDLE
        self._play_notification_sound()
        self._show_completion_dialog()
        
    def _break_complete(self):
        """Break timer done."""
        self.state = self.IDLE
        self._play_notification_sound()
        self._notify("Break's over!", "Ready for another pomodoro?")
        self._reset_timer()
        
    def _show_completion_dialog(self):
        """Show completion dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Complete!")
        dialog.configure(bg=self.BG)
        dialog.attributes('-topmost', True)
        dialog.geometry("340x160")
        dialog.resizable(False, False)
        # Don't use overrideredirect on macOS - causes focus issues
        # dialog.overrideredirect(True)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 340) // 2
        y = (dialog.winfo_screenheight() - 160) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Force focus to this dialog
        dialog.focus_force()
        dialog.grab_set()
        
        # Border effect
        border = tk.Frame(dialog, bg='#333333')
        border.pack(fill='both', expand=True, padx=1, pady=1)
        
        inner = tk.Frame(border, bg=self.BG)
        inner.pack(fill='both', expand=True)
        
        # Title
        tk.Label(
            inner, text="🍅 What did you accomplish?",
            font=('SF Pro', 13, 'bold'), fg=self.FG, bg=self.BG
        ).pack(pady=(15, 8))
        
        # Segment
        segment = self.segments[self.current_segment_idx]
        seg_frame = tk.Frame(inner, bg=self.BG)
        seg_frame.pack(pady=(0, 8))
        
        dot = tk.Canvas(seg_frame, width=10, height=10, bg=self.BG, highlightthickness=0)
        dot.pack(side='left', padx=(0, 5))
        dot.create_oval(1, 1, 9, 9, fill=segment['color'])
        
        tk.Label(seg_frame, text=segment['name'], font=('SF Pro', 10), 
                fg=self.FG_DIM, bg=self.BG).pack(side='left')
        
        # Entry
        entry_frame = tk.Frame(inner, bg=self.BG_LIGHT)
        entry_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        desc_entry = tk.Entry(
            entry_frame, font=('SF Pro', 11),
            bg=self.BG_LIGHT, fg=self.FG,
            insertbackground=self.FG, bd=0, relief='flat'
        )
        desc_entry.pack(fill='x', ipady=6, padx=6)
        
        # Force focus to entry after a small delay
        dialog.after(100, lambda: desc_entry.focus_force())
        
        def save_and_break():
            desc = desc_entry.get().strip() or "No description"
            if self.session_start_time:
                save_session(segment['id'], desc, 25, self.session_start_time)
            dialog.destroy()
            self._start_break()
            
        def save_and_skip():
            desc = desc_entry.get().strip() or "No description"
            if self.session_start_time:
                save_session(segment['id'], desc, 25, self.session_start_time)
            dialog.destroy()
            # Start next work cycle immediately instead of just resetting
            self._start_timer()
        
        # Buttons
        btn_frame = tk.Frame(inner, bg=self.BG)
        btn_frame.pack(pady=8)
        
        save_btn = tk.Label(
            btn_frame, text="Save & Break", font=('SF Pro', 10),
            fg=self.FG, bg='#2ecc71', padx=12, pady=4, cursor='hand2'
        )
        save_btn.pack(side='left', padx=4)
        save_btn.bind('<Button-1>', lambda e: save_and_break())
        save_btn.bind('<Enter>', lambda e: save_btn.config(bg='#27ae60'))
        save_btn.bind('<Leave>', lambda e: save_btn.config(bg='#2ecc71'))
        
        skip_btn = tk.Label(
            btn_frame, text="Skip Break", font=('SF Pro', 10),
            fg=self.FG, bg='#333333', padx=12, pady=4, cursor='hand2'
        )
        skip_btn.pack(side='left', padx=4)
        skip_btn.bind('<Button-1>', lambda e: save_and_skip())
        skip_btn.bind('<Enter>', lambda e: skip_btn.config(bg='#444444'))
        skip_btn.bind('<Leave>', lambda e: skip_btn.config(bg='#333333'))
        
        desc_entry.bind('<Return>', lambda e: save_and_break())
        dialog.bind('<Escape>', lambda e: save_and_skip())
        
    def _start_break(self):
        """Start break."""
        self.time_remaining = self.break_duration
        self.state = self.BREAK
        self.time_label.config(fg='#3498db')  # Blue for break
        self._update_time_display()
        self.play_btn.config(text="⏸")
        
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
        
    def _update_time_display(self):
        """Update display."""
        mins = self.time_remaining // 60
        secs = self.time_remaining % 60
        self.time_label.config(text=f"{mins:02d}:{secs:02d}")
        
    def _play_notification_sound(self):
        """Play sound."""
        if platform.system() == 'Darwin':
            subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], capture_output=True)
        else:
            self.root.bell()
            
    def _notify(self, title: str, message: str):
        """System notification."""
        if platform.system() == 'Darwin':
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], capture_output=True)
            
    def _open_dashboard(self):
        """Open dashboard."""
        import webbrowser
        webbrowser.open('http://localhost:5050')
    
    def _start_drag(self, event):
        """Start drag."""
        widget = event.widget
        if isinstance(widget, (ttk.Combobox,)):
            return
        # Don't drag if clicking on labels that are buttons
        if isinstance(widget, tk.Label) and widget.cget('cursor') == 'hand2':
            return
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def _drag(self, event):
        """Drag window."""
        if hasattr(self, '_drag_start_x'):
            x = self.root.winfo_x() + event.x - self._drag_start_x
            y = self.root.winfo_y() + event.y - self._drag_start_y
            self.root.geometry(f"+{x}+{y}")
    
    def _minimize(self):
        """Minimize."""
        self.root.withdraw()
        self.root.after(3000, self._restore)
        
    def _restore(self):
        """Restore."""
        self.root.deiconify()
        self.root.lift()
    
    def _keep_on_top(self):
        """Stay on top."""
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(500, self._keep_on_top)
    
    def _quit(self):
        """Quit."""
        self.running = False
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """Run."""
        self.root.mainloop()


if __name__ == "__main__":
    app = PomodoroTimer()
    app.run()