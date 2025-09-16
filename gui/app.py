import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import pandas as pd
import sys

from awards.pipeline import process_file

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # Set up main window properties
        self.title("MBBC Awards Processor (Y7–10)")
        self.geometry("760x520")
        self.minsize(720, 480)
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)  # temp folder created by PyInstaller
        else:
            base_path = Path(__file__).resolve().parent.parent  # project root

        icon_path = base_path / "logo.ico"

        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set icon: {e}")
        self.files = []           # List of selected Excel files
        self.out_dir = Path.cwd() # Output directory for processed files
        self._build()             # Build the GUI

    def _build(self):
        # Build the GUI layout and widgets

        # Top frame: label for selected files
        frm_top = ttk.Frame(self, padding=8); frm_top.pack(fill=tk.X)
        ttk.Label(frm_top, text="Selected files (XLSX):").pack(side=tk.LEFT)

        # Button frame: file and folder management buttons
        frm_btns = ttk.Frame(self, padding=(8, 0)); frm_btns.pack(fill=tk.X)
        ttk.Button(frm_btns, text="Add files", command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(frm_btns, text="Remove selected", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(frm_btns, text="Clear", command=self.clear_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(frm_btns, text="Output folder…", command=self.choose_out_dir).pack(side=tk.LEFT, padx=12)
        self.lbl_out = ttk.Label(frm_btns, text=f"Output: {self.out_dir}"); self.lbl_out.pack(side=tk.LEFT, padx=8)

        # List frame: shows selected files in a scrollable listbox
        frm_list = ttk.Frame(self, padding=8); frm_list.pack(fill=tk.BOTH, expand=True)
        self.lst = tk.Listbox(frm_list, selectmode=tk.EXTENDED, height=10)
        self.lst.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(frm_list, orient=tk.VERTICAL, command=self.lst.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y); self.lst.config(yscrollcommand=sb.set)

        # Run frame: process and quit buttons
        frm_run = ttk.Frame(self, padding=8); frm_run.pack(fill=tk.X)
        ttk.Button(frm_run, text="Process", command=self.process_all).pack(side=tk.LEFT)
        ttk.Button(frm_run, text="Quit", command=self.destroy).pack(side=tk.RIGHT)

        # Log frame: shows log messages in a text box
        frm_log = ttk.Frame(self, padding=8); frm_log.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm_log, text="Log:").pack(anchor=tk.W)
        self.txt = tk.Text(frm_log, height=10, wrap="word"); self.txt.pack(fill=tk.BOTH, expand=True)
        self.txt.configure(state=tk.DISABLED)

        # Status bar at the bottom
        self.status = ttk.Label(self, relief=tk.SUNKEN, anchor=tk.W); self.status.pack(fill=tk.X, side=tk.BOTTOM)

    def log(self, msg: str):
        # Log a message to the log text box and status bar
        self.txt.configure(state=tk.NORMAL)
        self.txt.insert(tk.END, msg + "\n")
        self.txt.see(tk.END)
        self.txt.configure(state=tk.DISABLED)
        self.status.config(text=msg)
        self.update_idletasks()

    def add_files(self):
        # Open file dialog to select Excel files and add them to the list
        paths = filedialog.askopenfilenames(title="Select XLSX files",
                                            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        for p in paths:
            pth = Path(p)
            if pth not in self.files:
                self.files.append(pth)
                self.lst.insert(tk.END, str(pth))

    def remove_selected(self):
        # Remove selected files from the list and internal storage
        sel = list(self.lst.curselection()); sel.reverse()
        for idx in sel:
            self.files.pop(idx)
            self.lst.delete(idx)

    def clear_files(self):
        # Clear all files from the list and internal storage
        self.files.clear()
        self.lst.delete(0, tk.END)

    def choose_out_dir(self):
        # Open folder dialog to select output directory
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            self.out_dir = Path(d)
            self.lbl_out.config(text=f"Output: {self.out_dir}")

    def process_all(self):
        # Process all selected files and show results
        if not self.files:
            messagebox.showwarning("No files", "Add at least one .xlsx file.")
            return
        pd.options.mode.copy_on_write = False
        ok = 0
        for p in self.files:
            outp = process_file(Path(p), self.out_dir, self.log)
            if outp:
                ok += 1
        messagebox.showinfo("Done", f"Processed {ok} file(s).")

def main():
    # Entry point: create and run the application
    app = App()
    app.mainloop()
