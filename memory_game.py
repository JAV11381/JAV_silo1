#!/usr/bin/env python3
"""
Daily Memory Sequence Game
A GUI-based memory training game where each day you must recall
all previously shown numbers in order.
"""

import json
import os
import random
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

SAVE_FILE = "memory_game_data.json"


def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Game logic helpers
# ---------------------------------------------------------------------------

def generate_number(num_digits: int) -> str:
    """Generate a random number with exactly num_digits digits (no leading zeros)."""
    low = 10 ** (num_digits - 1)
    high = (10 ** num_digits) - 1
    return str(random.randint(low, high))


def streak_key(num_digits: int, display_time: int) -> str:
    return f"{num_digits}d_{display_time}s"


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class MemoryGameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Daily Memory Sequence Game")
        self.geometry("700x550")
        self.resizable(False, False)
        self.configure(bg="#2c3e50")

        self.data = load_data()
        self.current_streak_key = None  # active streak key
        self.current_streak_info = None  # dict from data
        self.sequence = []  # numbers for current streak
        self.display_time = 3  # seconds
        self.num_digits = 2
        self.user_entries = []  # StringVars for input boxes
        self.timer_id = None

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#2c3e50")
        self.style.configure("TLabel", background="#2c3e50", foreground="#ecf0f1", font=("Helvetica", 12))
        self.style.configure("Header.TLabel", font=("Helvetica", 18, "bold"), foreground="#1abc9c")
        self.style.configure("TButton", font=("Helvetica", 12), padding=6)
        self.style.configure("Big.TButton", font=("Helvetica", 14, "bold"), padding=10)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.show_home_screen()

    # -----------------------------------------------------------------------
    # Screen helpers
    # -----------------------------------------------------------------------

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_home_screen(self):
        self.clear_frame()
        self.current_streak_key = None
        self.current_streak_info = None

        ttk.Label(self.main_frame, text="🧠 Daily Memory Sequence", style="Header.TLabel").pack(pady=(10, 20))

        ttk.Label(self.main_frame, text="Choose an existing streak or start a new one:").pack(pady=(0, 10))

        streaks = self.data.get("streaks", {})
        if streaks:
            list_frame = ttk.Frame(self.main_frame)
            list_frame.pack(pady=5, fill=tk.X)
            for key, info in streaks.items():
                streak_btn = ttk.Button(
                    list_frame,
                    text=f"{info['num_digits']} digits | {info['display_time']}s display | "
                         f"{len(info.get('history', []))} days played | Best score: {info.get('best_score', 0):.0%}",
                    command=lambda k=key: self.load_streak(k)
                )
                streak_btn.pack(pady=3, fill=tk.X)
        else:
            ttk.Label(self.main_frame, text="No saved streaks yet.").pack(pady=5)

        ttk.Button(self.main_frame, text="➕ Start New Streak", style="Big.TButton", command=self.show_setup_screen).pack(pady=20)

    def show_setup_screen(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="New Streak Setup", style="Header.TLabel").pack(pady=(10, 20))

        # Number of digits
        ttk.Label(self.main_frame, text="Number of digits per number:").pack(pady=(10, 5))
        self.digits_var = tk.StringVar(value="2")
        digits_spin = ttk.Spinbox(self.main_frame, from_=1, to=10, textvariable=self.digits_var, width=10, font=("Helvetica", 12))
        digits_spin.pack()

        # Display time
        ttk.Label(self.main_frame, text="Display time per new number (seconds):").pack(pady=(20, 5))
        self.time_var = tk.StringVar(value="3")
        time_spin = ttk.Spinbox(self.main_frame, from_=1, to=60, textvariable=self.time_var, width=10, font=("Helvetica", 12))
        time_spin.pack()

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=30)
        ttk.Button(btn_frame, text="Start", command=self.start_new_streak).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Back", command=self.show_home_screen).pack(side=tk.LEFT, padx=10)

    def show_streak_dashboard(self):
        self.clear_frame()
        info = self.current_streak_info
        history = info.get("history", [])
        days_played = len(history)
        best = info.get("best_score", 0.0)

        ttk.Label(self.main_frame, text=f"🔢 {info['num_digits']}-digit Streak", style="Header.TLabel").pack(pady=(10, 5))
        ttk.Label(self.main_frame, text=f"Display time: {info['display_time']}s | Days played: {days_played} | Best score: {best:.0%}").pack(pady=(0, 15))

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="▶ Play Today", style="Big.TButton", command=self.start_today_play).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="📈 View Progress Plot", command=self.show_plot).pack(side=tk.LEFT, padx=10)

        ttk.Button(self.main_frame, text="⬅ Back to Home", command=self.show_home_screen).pack(pady=20)

    def show_reveal_screen(self):
        """Show today's new number for the configured amount of seconds."""
        self.clear_frame()

        info = self.current_streak_info
        history = info.get("history", [])
        day_number = len(history) + 1

        # Generate today's number if not already generated for today
        today = today_str()
        if history and history[-1].get("date") == today and "number" in history[-1]:
            todays_num = history[-1]["number"]
        else:
            todays_num = generate_number(info["num_digits"])
            history.append({"date": today, "number": todays_num, "score": None})
            save_data(self.data)
            self.sequence = [h["number"] for h in history]

        self.sequence = [h["number"] for h in history]

        ttk.Label(self.main_frame, text=f"Day {day_number}", style="Header.TLabel").pack(pady=(20, 10))
        ttk.Label(self.main_frame, text="Memorize this number:", font=("Helvetica", 14)).pack(pady=10)

        num_label = tk.Label(self.main_frame, text=todays_num, font=("Helvetica", 64, "bold"), fg="#1abc9c", bg="#2c3e50")
        num_label.pack(pady=20)

        self.countdown_var = tk.IntVar(value=info["display_time"])
        countdown_label = ttk.Label(self.main_frame, textvariable=self.countdown_var, font=("Helvetica", 16))
        countdown_label.pack(pady=10)

        self.countdown(info["display_time"], num_label, countdown_label)

    def show_input_screen(self):
        """Show input fields for all numbers from day 1 to today."""
        self.clear_frame()
        info = self.current_streak_info
        history = info.get("history", [])
        day_number = len(history)

        ttk.Label(self.main_frame, text=f"Day {day_number} - Recall", style="Header.TLabel").pack(pady=(10, 10))
        ttk.Label(self.main_frame, text="Type the numbers in order from Day 1 to today:").pack(pady=(0, 10))

        # Scrollable frame in case many days
        canvas = tk.Canvas(self.main_frame, bg="#2c3e50", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.user_entries = []
        for i in range(day_number):
            row = ttk.Frame(scroll_frame)
            row.pack(fill=tk.X, pady=4)
            ttk.Label(row, text=f"Day {i + 1}:", width=8).pack(side=tk.LEFT)
            entry = ttk.Entry(row, font=("Helvetica", 14), width=15)
            entry.pack(side=tk.LEFT, padx=5)
            self.user_entries.append(entry)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(self.main_frame, text="Submit", style="Big.TButton", command=self.check_answers).pack(pady=15)

    def show_result_screen(self, correct_count, total, score_pct):
        self.clear_frame()
        status = "✅ RIGHT" if score_pct == 1.0 else "❌ WRONG"

        ttk.Label(self.main_frame, text="Result", style="Header.TLabel").pack(pady=(20, 10))
        ttk.Label(self.main_frame, text=status, font=("Helvetica", 28, "bold")).pack(pady=10)
        ttk.Label(self.main_frame, text=f"{correct_count} / {total} correct ({score_pct:.0%})").pack(pady=10)

        # Show correct sequence for reference
        info = self.current_streak_info
        history = info.get("history", [])
        seq_frame = ttk.Frame(self.main_frame)
        seq_frame.pack(pady=10)
        for i, h in enumerate(history):
            color = "#2ecc71" if i < correct_count and self.user_entries[i].get().strip() == h["number"] else "#e74c3c"
            lbl = tk.Label(seq_frame, text=h["number"], font=("Helvetica", 12, "bold"), fg=color, bg="#2c3e50")
            lbl.pack(side=tk.LEFT, padx=4)

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="📈 View Plot", command=self.show_plot).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="🏠 Home", command=self.show_home_screen).pack(side=tk.LEFT, padx=10)

    def show_plot(self):
        """Open a new window with a score-vs-days plot for the current streak."""
        if self.current_streak_key is None:
            messagebox.showinfo("Info", "No streak selected.")
            return

        info = self.current_streak_info
        history = info.get("history", [])
        days = list(range(1, len(history) + 1))
        scores = [h.get("score", 0.0) for h in history]

        if not days:
            messagebox.showinfo("Info", "No data to plot yet.")
            return

        plot_win = tk.Toplevel(self)
        plot_win.title(f"Progress: {info['num_digits']}-digit Streak")
        plot_win.geometry("600x450")
        plot_win.configure(bg="#2c3e50")

        fig, ax = plt.subplots(figsize=(6, 4), facecolor="#2c3e50")
        ax.set_facecolor="#34495e"
        ax.plot(days, scores, marker="o", linestyle="-", color="#1abc9c", linewidth=2, markersize=8)
        ax.set_xlabel("Day", color="white")
        ax.set_ylabel("Score (% correct)", color="white")
        ax.set_title(f"Score vs Days ({info['num_digits']} digits, {info['display_time']}s)", color="white")
        ax.tick_params(colors="white")
        ax.set_ylim(0, 1.05)
        ax.set_xticks(days)
        ax.grid(True, color="#7f8c8d", linestyle="--", alpha=0.5)
        ax.spines["bottom"].set_color("white")
        ax.spines["top"].set_color("white")
        ax.spines["left"].set_color("white")
        ax.spines["right"].set_color("white")

        canvas = FigureCanvasTkAgg(fig, master=plot_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # -----------------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------------

    def start_new_streak(self):
        try:
            num_digits = int(self.digits_var.get())
            display_time = int(self.time_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integers.")
            return

        if num_digits < 1 or display_time < 1:
            messagebox.showerror("Error", "Values must be at least 1.")
            return

        key = streak_key(num_digits, display_time)
        if "streaks" not in self.data:
            self.data["streaks"] = {}

        if key not in self.data["streaks"]:
            self.data["streaks"][key] = {
                "num_digits": num_digits,
                "display_time": display_time,
                "history": [],
                "best_score": 0.0,
            }
            save_data(self.data)

        self.load_streak(key)

    def load_streak(self, key):
        self.current_streak_key = key
        self.current_streak_info = self.data["streaks"][key]
        self.num_digits = self.current_streak_info["num_digits"]
        self.display_time = self.current_streak_info["display_time"]
        self.sequence = [h["number"] for h in self.current_streak_info.get("history", [])]
        self.show_streak_dashboard()

    def start_today_play(self):
        self.show_reveal_screen()

    def countdown(self, remaining, num_label, countdown_label):
        if remaining <= 0:
            num_label.destroy()
            countdown_label.destroy()
            self.show_input_screen()
            return
        self.countdown_var.set(remaining)
        self.timer_id = self.after(1000, lambda: self.countdown(remaining - 1, num_label, countdown_label))

    def check_answers(self):
        info = self.current_streak_info
        history = info.get("history", [])
        total = len(history)
        correct = 0

        for i, entry in enumerate(self.user_entries):
            user_val = entry.get().strip()
            if i < total and user_val == history[i]["number"]:
                correct += 1

        score = correct / total if total > 0 else 0.0
        # Update today's score in history (last entry)
        if history:
            history[-1]["score"] = score
        if score > info.get("best_score", 0.0):
            info["best_score"] = score
        save_data(self.data)

        self.show_result_screen(correct, total, score)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = MemoryGameApp()
    app.mainloop()
