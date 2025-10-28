# this is for when task manager is disabled and ollama needs to stop geeking
import threading
import psutil
import tkinter as tk
from tkinter import ttk, messagebox
import queue
import time
import os
import signal

###############################################################################
# ProcessFetcher runs in a background thread and gathers process info without
# blocking the GUI. It pushes results into a queue for the main thread.
###############################################################################
class ProcessFetcher(threading.Thread):
    def __init__(self, result_queue, poll_interval=1.0):
        super().__init__(daemon=True)
        self.result_queue = result_queue
        self.poll_interval = poll_interval
        self.filter_text = ""
        self._stop_flag = False

    def set_filter(self, text):
        self.filter_text = text.lower().strip()

    def stop(self):
        self._stop_flag = True

    def run(self):
        while not self._stop_flag:
            processes = []
            for proc in psutil.process_iter(
                attrs=["pid", "name", "cpu_percent", "memory_percent"]
            ):
                try:
                    info = proc.info
                    # basic filter by substring in name
                    if self.filter_text and self.filter_text not in info["name"].lower():
                        continue
                    processes.append(
                        {
                            "name": info["name"],
                            "pid": info["pid"],
                            "cpu": info["cpu_percent"],
                            "mem": info["memory_percent"],
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process ended or we can't touch it. Ignore.
                    continue

            # sort by CPU desc just so it's nicer to read
            processes.sort(key=lambda p: p["cpu"], reverse=True)

            # push to queue for GUI
            try:
                self.result_queue.put_nowait(processes)
            except queue.Full:
                # if GUI hasn't handled old data yet, we drop the new one
                pass

            time.sleep(self.poll_interval)


###############################################################################
# Main GUI Application
###############################################################################
class TaskManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Not Sketchy Task Manager 🔬")

        # Queue for cross-thread data passing
        self.result_queue = queue.Queue(maxsize=1)

        # Background fetcher thread
        self.fetcher = ProcessFetcher(self.result_queue, poll_interval=1.0)
        self.fetcher.start()

        # Build UI
        self._build_widgets()

        # Start polling for new process lists from background thread
        self._schedule_queue_check()

    def _build_widgets(self):
        # --- Top frame: Search box + Search button + End Task button
        top_frame = ttk.Frame(self.root, padding=8)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top_frame, text="Search:").pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=4)

        self.search_button = ttk.Button(
            top_frame, text="Apply Filter", command=self.apply_filter
        )
        self.search_button.pack(side=tk.LEFT, padx=4)

        self.clear_button = ttk.Button(
            top_frame, text="Clear Filter", command=self.clear_filter
        )
        self.clear_button.pack(side=tk.LEFT, padx=4)

        self.kill_button = ttk.Button(
            top_frame, text="End Task", command=self.end_task
        )
        self.kill_button.pack(side=tk.RIGHT, padx=4)

        # --- Treeview for process list
        columns = ("name", "pid", "cpu", "mem")
        self.tree = ttk.Treeview(
            self.root,
            columns=columns,
            show="headings",
            height=20,
        )
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tree.heading("name", text="Name")
        self.tree.heading("pid", text="PID")
        self.tree.heading("cpu", text="CPU %")
        self.tree.heading("mem", text="Mem %")

        self.tree.column("name", width=220, anchor=tk.W)
        self.tree.column("pid", width=70, anchor=tk.CENTER)
        self.tree.column("cpu", width=60, anchor=tk.CENTER)
        self.tree.column("mem", width=60, anchor=tk.CENTER)

        # Vertical scrollbar
        vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Status bar
        self.status_var = tk.StringVar(value="Ready.")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=4,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def apply_filter(self):
        text = self.search_var.get()
        self.fetcher.set_filter(text)
        self.status_var.set(f"Filter applied: {text if text else '(none)'}")

    def clear_filter(self):
        self.search_var.set("")
        self.fetcher.set_filter("")
        self.status_var.set("Filter cleared.")

    def end_task(self):
        # get selected process
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("End Task", "No process selected.")
            return

        item_id = selection[0]
        pid = int(self.tree.set(item_id, "pid"))
        name = self.tree.set(item_id, "name")

        # mild safety: confirm
        answer = messagebox.askyesno(
            "End Task",
            f"Really end {name} (PID {pid})?",
        )
        if not answer:
            return

        try:
            # On Windows, best shot is psutil.Process(pid).terminate()
            # On Linux/macOS, terminate() sends SIGTERM, which is polite.
            proc = psutil.Process(pid)
            proc.terminate()
            # optional: force kill if it doesn't exit fast enough.
            # We'll use a short wait loop.
            gone, alive = psutil.wait_procs([proc], timeout=2)
            if alive:
                # try kill (SIGKILL / TerminateProcess)
                for p in alive:
                    try:
                        p.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        messagebox.showerror(
                            "End Task",
                            f"Could not force kill {name} (PID {pid}): {e}",
                        )
                        return
            self.status_var.set(f"Ended {name} (PID {pid}).")
        except psutil.NoSuchProcess:
            self.status_var.set("Process already ended.")
        except psutil.AccessDenied:
            messagebox.showerror(
                "End Task",
                "Access denied. You might not have permission to kill that process.",
            )
        except Exception as e:
            messagebox.showerror("End Task", f"Error: {e}")

    def _schedule_queue_check(self):
        """
        Periodically run in the main thread.
        Check if the worker thread gave us a new process list.
        If so, update the table.
        """
        try:
            processes = self.result_queue.get_nowait()
        except queue.Empty:
            processes = None

        if processes is not None:
            self._update_table(processes)

        # Schedule again in ~500ms
        self.root.after(500, self._schedule_queue_check)

    def _update_table(self, process_list):
        # wipe current rows
        self.tree.delete(*self.tree.get_children())

        # repopulate
        for proc in process_list:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    proc["name"],
                    proc["pid"],
                    f"{proc['cpu']:.1f}",
                    f"{proc['mem']:.1f}",
                ),
            )

        self.status_var.set(f"Processes: {len(process_list)}")

    def on_close(self):
        # tell background thread to stop
        self.fetcher.stop()
        self.root.destroy()


def main():
    # On first call, psutil cpu_percent() needs a baseline. This warms it up.
    for p in psutil.process_iter():
        try:
            p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    root = tk.Tk()
    app = TaskManagerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
