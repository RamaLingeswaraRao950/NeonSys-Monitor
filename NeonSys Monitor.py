from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk
import tkinter as tk
import psutil
import time
import os
from datetime import timedelta
import colorsys

# --- Settings ---
UPDATE_INTERVAL = 1000  # ms
MAX_POINTS = 60  # keep last 60 seconds of data

# Data storage
cpu_history = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
ram_history = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
net_up_history = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
net_down_history = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)

last_net = psutil.net_io_counters()

# --- Tkinter App ---
root = tk.Tk()
root.title("⚡NeonSys Monitor ⚡")
root.geometry("929x929")
root.configure(bg="#1e1e2e")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#1e1e2e",
                foreground="white", font=("Segoe UI", 11, "bold"))

# --- Animated Gradient Background ---
gradient_frame = tk.Frame(root, bg="#1e1e2e")
gradient_frame.pack(fill=tk.BOTH, expand=True)
canvas_bg = tk.Canvas(gradient_frame, highlightthickness=0)
canvas_bg.pack(fill=tk.BOTH, expand=True)

gradient_colors = [(30, 30, 46), (50, 50, 80), (70, 70, 100)]
hue = 0


def animate_bg():
    global hue
    w = canvas_bg.winfo_width()
    h = canvas_bg.winfo_height()
    canvas_bg.delete("all")
    # generate dynamic gradient
    for i in range(h):
        r, g, b = colorsys.hsv_to_rgb((hue + i/h) % 1, 0.5, 0.2 + i/h*0.5)
        color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
        canvas_bg.create_line(0, i, w, i, fill=color)
    hue += 0.002
    root.after(50, animate_bg)


animate_bg()

# --- Info Labels ---
info_frame = tk.Frame(canvas_bg, bg="#1e1e2e")
info_frame.place(relx=0.5, rely=0.02, anchor="n")

cpu_label = ttk.Label(info_frame, text="CPU: ")
cpu_label.pack(pady=5)
ram_label = ttk.Label(info_frame, text="RAM: ")
ram_label.pack(pady=5)
disk_label = ttk.Label(info_frame, text="Disk: ")
disk_label.pack(pady=5)
net_label = ttk.Label(info_frame, text="Network: ")
net_label.pack(pady=5)
uptime_label = ttk.Label(info_frame, text="Uptime: ")
uptime_label.pack(pady=5)

# --- Matplotlib Figure ---
fig, axs = plt.subplots(3, 1, figsize=(8, 6), dpi=100)
fig.patch.set_facecolor("#1e1e2e")

for ax in axs:
    ax.set_facecolor("#2e2e3e")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("white")

axs[0].set_title("CPU Usage (%)", color="white")
axs[1].set_title("RAM Usage (%)", color="white")
axs[2].set_title("Network Speed (KB/s)", color="white")

cpu_line, = axs[0].plot(cpu_history, color="lime", linewidth=2)
ram_line, = axs[1].plot(ram_history, color="cyan", linewidth=2)
net_up_line, = axs[2].plot(
    net_up_history, color="orange", linewidth=2, label="Upload")
net_down_line, = axs[2].plot(
    net_down_history, color="yellow", linewidth=2, label="Download")
axs[2].legend(facecolor="#2e2e3e", labelcolor="white")

canvas = FigureCanvasTkAgg(fig, master=canvas_bg)
canvas.get_tk_widget().place(relx=0.5, rely=0.25, anchor="n")

# --- Animated label colors ---


def animate_labels():
    t = time.time()
    for lbl in [cpu_label, ram_label, disk_label, net_label, uptime_label]:
        r = int((1 + (0.5 + 0.5 * (time.time() % 1))) * 128) % 255
        g = int((1 + (0.3 + 0.7 * (time.time() % 1))) * 128) % 255
        b = int((1 + (0.6 + 0.4 * (time.time() % 1))) * 128) % 255
        lbl.config(foreground=f"#{r:02x}{g:02x}{b:02x}")
    root.after(200, animate_labels)


animate_labels()

# --- Update Function ---


def update_stats():
    global last_net

    # CPU
    cpu = psutil.cpu_percent(interval=None)
    cpu_label.config(text=f"CPU: {cpu}%")
    cpu_history.append(cpu)

    # RAM
    ram = psutil.virtual_memory()
    ram_label.config(
        text=f"RAM: {ram.percent}% ({round(ram.used/1e9, 1)} GB / {round(ram.total/1e9, 1)} GB)")
    ram_history.append(ram.percent)

    # Disk
    disk = psutil.disk_usage('/')
    disk_label.config(
        text=f"Disk: {disk.percent}% ({round(disk.used/1e9, 1)} GB / {round(disk.total/1e9, 1)} GB)")

    # Network
    new_net = psutil.net_io_counters()
    upload_speed = (new_net.bytes_sent - last_net.bytes_sent) / 1024
    download_speed = (new_net.bytes_recv - last_net.bytes_recv) / 1024
    net_label.config(
        text=f"Network: ↑ {round(upload_speed, 1)} KB/s | ↓ {round(download_speed, 1)} KB/s")
    net_up_history.append(upload_speed)
    net_down_history.append(download_speed)
    last_net = new_net

    # Uptime
    boot_time = psutil.boot_time()
    uptime = timedelta(seconds=int(time.time() - boot_time))
    uptime_label.config(text=f"Uptime: {uptime}")

    # Update plots
    cpu_line.set_ydata(cpu_history)
    cpu_line.set_xdata(range(len(cpu_history)))
    axs[0].set_ylim(0, 100)

    ram_line.set_ydata(ram_history)
    ram_line.set_xdata(range(len(ram_history)))
    axs[1].set_ylim(0, 100)

    net_up_line.set_ydata(net_up_history)
    net_up_line.set_xdata(range(len(net_up_history)))
    net_down_line.set_ydata(net_down_history)
    net_down_line.set_xdata(range(len(net_down_history)))
    axs[2].set_ylim(0, max(max(net_up_history), max(net_down_history), 10))

    canvas.draw()
    root.after(UPDATE_INTERVAL, update_stats)


# --- Run ---
update_stats()
root.mainloop()
