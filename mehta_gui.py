#!/usr/bin/env python3
"""
Mehta 3/3 Screener — Zero-Dependency Windows GUI
Requires: only Python 3.8+ (tkinter is built-in on Windows)
"""

import json
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd

BASE = Path(__file__).resolve().parent
CFG_PATH = BASE / "config.json"
OUTPUT_DIR = BASE / "output"


class ScreenerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mehta 3/3 NSE Screener")
        self.root.geometry("1100x750")
        self.root.configure(bg="#f5f6fa")
        self.root.minsize(900, 600)

        # Style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#f5f6fa")
        self.style.configure("TLabel", background="#f5f6fa", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"), foreground="#2c3e50")
        self.style.configure("Sub.TLabel", font=("Segoe UI", 11), foreground="#7f8c8d")
        self.style.configure("Run.TButton", font=("Segoe UI", 12, "bold"))
        self.style.configure("Green.TButton", foreground="white", background="#27ae60")
        self.style.configure("Red.TButton", foreground="white", background="#e74c3c")

        self.build_ui()
        self.check_existing_run()

    def build_ui(self):
        # Header
        header = ttk.Frame(self.root, padding=(20, 15))
        header.pack(fill="x")

        ttk.Label(header, text="📊 Mehta 3/3 NSE Screener", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="One-click screening | Auto-filtered 3/3 & 2/3 results", style="Sub.TLabel").pack(anchor="w")

        # Control Panel
        ctrl = ttk.Frame(self.root, padding=(20, 10))
        ctrl.pack(fill="x")

        self.run_btn = ttk.Button(ctrl, text="🚀 RUN SCREENER", command=self.start_screener, style="Run.TButton")
        self.run_btn.pack(side="left", padx=(0, 10))

        ttk.Button(ctrl, text="📂 Open Output Folder", command=self.open_output).pack(side="left", padx=5)
        ttk.Button(ctrl, text="⬇️ Export Filtered CSV", command=self.export_csv).pack(side="left", padx=5)
        ttk.Button(ctrl, text="📋 Copy Symbols", command=self.copy_symbols).pack(side="left", padx=5)

        # Progress
        prog_frame = ttk.Frame(self.root, padding=(20, 5))
        prog_frame.pack(fill="x")

        self.progress = ttk.Progressbar(prog_frame, mode="indeterminate", length=300)
        self.status = ttk.Label(prog_frame, text="Ready", font=("Segoe UI", 9, "italic"))

        # Stats Cards
        stats = ttk.Frame(self.root, padding=(20, 10))
        stats.pack(fill="x")

        self.stat_labels = {}
        colors = [("#11998e", "3/3 Super"), ("#f7971e", "2/3 Hold"), ("#ee5a6f", "0-1/3 Exit"), ("#667eea", "Total")]
        for i, (color, title) in enumerate(colors):
            card = tk.Frame(stats, bg=color, bd=0, highlightthickness=0)
            card.pack(side="left", expand=True, fill="both", padx=5, pady=5)
            tk.Label(card, text=title, bg=color, fg="white", font=("Segoe UI", 10)).pack(pady=(8, 0))
            lbl = tk.Label(card, text="—", bg=color, fg="white", font=("Segoe UI", 18, "bold"))
            lbl.pack(pady=(0, 8))
            self.stat_labels[title] = lbl

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root, padding=(20, 10))
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        # Tab 1: Filtered Results (3/3 + 2/3)
        self.tab_filtered = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_filtered, text="🎯 Filtered (3/3 + 2/3)")

        cols = ("Symbol", "Company", "Score", "Action", "Industry", "Price", "ATH", "52W Return",
                "Beats Nifty", "Beats Sector", "Record PAT", "Status")
        self.tree_filtered = ttk.Treeview(self.tab_filtered, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree_filtered.heading(c, text=c)
            self.tree_filtered.column(c, width=90, anchor="center")
        self.tree_filtered.column("Company", width=180, anchor="w")
        self.tree_filtered.column("Action", width=180, anchor="w")

        vsb = ttk.Scrollbar(self.tab_filtered, orient="vertical", command=self.tree_filtered.yview)
        hsb = ttk.Scrollbar(self.tab_filtered, orient="horizontal", command=self.tree_filtered.xview)
        self.tree_filtered.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree_filtered.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tab_filtered.grid_rowconfigure(0, weight=1)
        self.tab_filtered.grid_columnconfigure(0, weight=1)

        # Tab 2: All Results
        self.tab_all = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_all, text="📋 All Stocks")

        self.tree_all = ttk.Treeview(self.tab_all, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree_all.heading(c, text=c)
            self.tree_all.column(c, width=90, anchor="center")
        self.tree_all.column("Company", width=180, anchor="w")
        self.tree_all.column("Action", width=180, anchor="w")

        vsb2 = ttk.Scrollbar(self.tab_all, orient="vertical", command=self.tree_all.yview)
        hsb2 = ttk.Scrollbar(self.tab_all, orient="horizontal", command=self.tree_all.xview)
        self.tree_all.configure(yscrollcommand=vsb2.set, xscrollcommand=hsb2.set)
        self.tree_all.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")
        hsb2.grid(row=1, column=0, sticky="ew")
        self.tab_all.grid_rowconfigure(0, weight=1)
        self.tab_all.grid_columnconfigure(0, weight=1)

        # Tab 3: Logs
        self.tab_logs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_logs, text="📜 Logs")

        self.log_text = tk.Text(self.tab_logs, wrap="word", font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Footer
        footer = ttk.Frame(self.root, padding=(20, 5))
        footer.pack(fill="x", side="bottom")
        ttk.Label(footer, text="Mehta 3/3 Screener | Data: Yahoo Finance + Screener.in", foreground="#95a5a6").pack(side="left")
        self.file_label = ttk.Label(footer, text="", foreground="#3498db")
        self.file_label.pack(side="right")

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{datetime.now().strftime('%H:%M:%S')}  {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def set_status(self, text):
        self.status.configure(text=text)
        self.root.update_idletasks()

    def start_screener(self):
        self.run_btn.configure(state="disabled")
        self.progress.pack(side="left", padx=(0, 10))
        self.progress.start(10)
        self.status.pack(side="left")
        self.set_status("Running screener... please wait (2–5 min)")

        # Clear trees
        for item in self.tree_filtered.get_children():
            self.tree_filtered.delete(item)
        for item in self.tree_all.get_children():
            self.tree_all.delete(item)

        thread = threading.Thread(target=self._run_screener_thread, daemon=True)
        thread.start()

    def _run_screener_thread(self):
        script = BASE / "mehta_screener.py"
        if not script.exists():
            self.root.after(0, lambda: messagebox.showerror("Error", "mehta_screener.py not found!"))
            self.root.after(0, self.reset_ui)
            return

        try:
            self.root.after(0, lambda: self.log("Starting mehta_screener.py..."))
            proc = subprocess.Popen(
                [sys.executable, str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(BASE),
            )
            for line in proc.stdout:
                self.root.after(0, lambda l=line.strip(): self.log(l))
            proc.wait()

            if proc.returncode == 0:
                self.root.after(0, lambda: self.log("✅ Screener finished successfully."))
                self.root.after(0, self.load_results)
                self.root.after(0, lambda: messagebox.showinfo("Done", "Screener completed! Filtered results loaded."))
            else:
                self.root.after(0, lambda: self.log("❌ Screener exited with errors."))
                self.root.after(0, lambda: messagebox.showerror("Error", "Screener failed. Check Logs tab."))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.status.pack_forget()
        self.run_btn.configure(state="normal")

    def load_results(self):
        latest = self.get_latest_excel()
        if not latest:
            return

        self.file_label.configure(text=f"File: {latest.name}")
        self.log(f"Loading: {latest.name}")

        try:
            xls = pd.ExcelFile(latest)
            all_data = []

            # Load all sheets
            for sheet in xls.sheet_names:
                if sheet == "SUMMARY":
                    continue
                df = pd.read_excel(xls, sheet_name=sheet)
                df["Sheet"] = sheet
                all_data.append(df)

            if not all_data:
                return

            full_df = pd.concat(all_data, ignore_index=True)

            # Filtered: only 3/3 and 2/3
            filtered_df = full_df[full_df["Score"].isin(["3/3", "2/3"])].copy()

            # Update stats
            counts = full_df["Score"].value_counts().to_dict()
            self.stat_labels["3/3 Super"].configure(text=str(counts.get("3/3", 0)))
            self.stat_labels["2/3 Hold"].configure(text=str(counts.get("2/3", 0)))
            self.stat_labels["0-1/3 Exit"].configure(text=str(counts.get("1/3", 0) + counts.get("0/3", 0)))
            self.stat_labels["Total"].configure(text=str(len(full_df)))

            # Populate Filtered tree
            for _, row in filtered_df.iterrows():
                vals = (
                    row.get("Symbol", ""), row.get("Company", ""), row.get("Score", ""),
                    row.get("Action", ""), row.get("Industry", ""),
                    f"{row.get('Current Price', 0):.2f}" if pd.notna(row.get('Current Price')) else "",
                    f"{row.get('ATH', 0):.2f}" if pd.notna(row.get('ATH')) else "",
                    f"{row.get('52W Return', 0):.2%}" if pd.notna(row.get('52W Return')) else "",
                    "✅" if row.get("Beats Nifty500") else "❌",
                    "✅" if row.get("Beats Sector") else "❌",
                    "✅" if row.get("Record PAT?") else "❌",
                    row.get("Data Status", "")
                )
                self.tree_filtered.insert("", "end", values=vals)

            # Populate All tree
            for _, row in full_df.iterrows():
                vals = (
                    row.get("Symbol", ""), row.get("Company", ""), row.get("Score", ""),
                    row.get("Action", ""), row.get("Industry", ""),
                    f"{row.get('Current Price', 0):.2f}" if pd.notna(row.get('Current Price')) else "",
                    f"{row.get('ATH', 0):.2f}" if pd.notna(row.get('ATH')) else "",
                    f"{row.get('52W Return', 0):.2%}" if pd.notna(row.get('52W Return')) else "",
                    "✅" if row.get("Beats Nifty500") else "❌",
                    "✅" if row.get("Beats Sector") else "❌",
                    "✅" if row.get("Record PAT?") else "❌",
                    row.get("Data Status", "")
                )
                tag = "green" if row.get("Score") == "3/3" else "orange" if row.get("Score") == "2/3" else "red"
                self.tree_all.insert("", "end", values=vals, tags=(tag,))

            self.tree_all.tag_configure("green", background="#d5f5e3")
            self.tree_all.tag_configure("orange", background="#fdebd0")
            self.tree_all.tag_configure("red", background="#fadbd8")

            self.log(f"Loaded {len(filtered_df)} filtered stocks ({len(full_df)} total).")

        except Exception as e:
            self.log(f"Error loading Excel: {e}")
            messagebox.showerror("Load Error", str(e))

    def get_latest_excel(self):
        if not OUTPUT_DIR.exists():
            return None
        files = sorted(OUTPUT_DIR.glob("Mehta_Screener_*.xlsx"), reverse=True)
        return files[0] if files else None

    def check_existing_run(self):
        latest = self.get_latest_excel()
        if latest:
            self.file_label.configure(text=f"Last run: {latest.name}")
            self.load_results()

    def open_output(self):
        p = OUTPUT_DIR if OUTPUT_DIR.exists() else BASE
        webbrowser.open(str(p))

    def export_csv(self):
        latest = self.get_latest_excel()
        if not latest:
            messagebox.showwarning("No Data", "Run the screener first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"Mehta_Filtered_{datetime.now().strftime('%Y-%m-%d')}.csv"
        )
        if not path:
            return

        try:
            xls = pd.ExcelFile(latest)
            dfs = []
            for sheet in xls.sheet_names:
                if sheet in ("3-3 SUPER", "2-3 HOLD"):
                    dfs.append(pd.read_excel(xls, sheet_name=sheet))
            if dfs:
                pd.concat(dfs).to_csv(path, index=False)
                messagebox.showinfo("Exported", f"Saved to:\n{path}")
            else:
                messagebox.showwarning("No Data", "No 3/3 or 2/3 sheets found.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def copy_symbols(self):
        items = self.tree_filtered.selection()
        if not items:
            items = self.tree_filtered.get_children()

        symbols = [self.tree_filtered.item(i, "values")[0] for i in items]
        if symbols:
            self.root.clipboard_clear()
            self.root.clipboard_append(", ".join(symbols))
            messagebox.showinfo("Copied", f"{len(symbols)} symbols copied to clipboard.")


def main():
    root = tk.Tk()
    app = ScreenerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()