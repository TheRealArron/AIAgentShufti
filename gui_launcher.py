# gui_launcher.py
import tkinter as tk
from tkinter import messagebox, scrolledtext
import asyncio
import threading
from ai_job_agent import run_agent_with_name

# Function to run off-sync loop
def start_agent():
    email = email_entry.get()
    password = password_entry.get()
    name = name_entry.get()
    skills = skills_entry.get().split(',')  # Get skills as a comma-separated string and split them

    if not email or not password or not name:
        messagebox.showerror("Error", "Please enter email, password, and name.")
        return

    start_button.config(state=tk.DISABLED)
    append_log("Starting agent...\n")

    def run_async_task():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_agent_with_name(email, password, name, skills, log_callback=append_log))
        except Exception as e:
            append_log(f"[ERROR] {e}\n")
        finally:
            append_log("Agent process finished.\n")
            start_button.config(state=tk.NORMAL)
            loop.close()

    threading.Thread(target=run_async_task, daemon=True).start()

def append_log(message):
    status_box.insert(tk.END, message)
    status_box.see(tk.END)
    with open("session_log.txt", "a") as f:
        f.write(message)

# GUI layout
root = tk.Tk()
root.title("AI Job Agent")

# Entries
tk.Label(root, text="Email:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
tk.Label(root, text="Password:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
tk.Label(root, text="Agent Name:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
tk.Label(root, text="Skills (comma separated):").grid(row=3, column=0, padx=10, pady=5, sticky="e")

email_entry = tk.Entry(root, width=40)
password_entry = tk.Entry(root, width=40, show="*")
name_entry = tk.Entry(root, width=40)
skills_entry = tk.Entry(root, width=40)

email_entry.grid(row=0, column=1, padx=10, pady=5)
password_entry.grid(row=1, column=1, padx=10, pady=5)
name_entry.grid(row=2, column=1, padx=10, pady=5)
skills_entry.grid(row=3, column=1, padx=10, pady=5)

start_button = tk.Button(root, text="Start Agent", command=start_agent)
start_button.grid(row=4, column=0, columnspan=2, pady=10)

# Status Box
tk.Label(root, text="Status:").grid(row=5, column=0, columnspan=2)
status_box = scrolledtext.ScrolledText(root, width=70, height=20, state=tk.NORMAL)
status_box.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

root.mainloop()
