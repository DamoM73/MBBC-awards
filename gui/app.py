import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import pandas as pd

from awards.pipeline import process_file

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MBBC Awards Processor (Y7–10)")
        self.geometry("760x520")
        self.minsize(720, 480)
        self.files = []
        self.out_dir = Path.cwd()
        self._build()

    def _build(self):
        frm_top = ttk.Frame(self, padding=8); frm_top.pack(fill=tk.X)
        ttk.Label(frm_top, text="Selected files (XLSX):").pack(side=tk.LEFT)

        frm_btns = ttk.Frame(self, padding=(8, 0)); frm_btns.pack(fill=tk.X)
        ttk.Button(frm_btns, text="Add files", command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(frm_btns, text="Remove selected", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(frm_btns, text="Clear", command=self.clear_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(frm_btns, text="Output folder…", command=self.choose_out_dir).pack(side=tk.LEFT, padx=12)
        self.lbl_out = ttk.Label(frm_btns, text=f"Output: {self.out_dir}"); self.lbl_out.pack(side=tk.LEFT, padx=8)

        frm_list = ttk.Frame(self, padding=8); frm_list.pack(fill=tk.BOTH, expand=True)
        self.lst = tk.Listbox(frm_list, selectmode=tk.EXTENDED, height=10)
        self.lst.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(frm_list, orient=tk.VERTICAL, command=self.lst.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y); self.lst.config(yscrollcommand=sb.set)

        frm_run = ttk.Frame(self, padding=8); frm_run.pack(fill=tk.X)
        ttk.Button(frm_run, text="Process", command=self.process_all).pack(side=tk.LEFT)
        ttk.Button(frm_run, text="Quit", command=self.destroy).pack(side=tk.RIGHT)

        frm_log = ttk.Frame(self, padding=8); frm_log.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm_log, text="Log:").pack(anchor=tk.W)
        self.txt = tk.Text(frm_log, height=10, wrap="word"); self.txt.pack(fill=tk.BOTH, expand=True)
        self.txt.configure(state=tk.DISABLED)

        self.status = ttk.Label(self, relief=tk.SUNKEN, anchor=tk.W); self.status.pack(fill=tk.X, side=tk.BOTTOM)

    def log(self, msg: str):
        self.txt.configure(state=tk.NORMAL)
        self.txt.insert(tk.END, msg + "\n")
        self.txt.see(tk.END)
        self.txt.configure(state=tk.DISABLED)
        self.status.config(text=msg)
        self.update_idletasks()

    def add_files(self):
        paths = filedialog.askopenfilenames(title="Select XLSX files",
                                            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        for p in paths:
            pth = Path(p)
            if pth not in self.files:
                self.files.append(pth)
                self.lst.insert(tk.END, str(pth))

    def remove_selected(self):
        sel = list(self.lst.curselection()); sel.reverse()
        for idx in sel:
            self.files.pop(idx)
            self.lst.delete(idx)

    def clear_files(self):
        self.files.clear()
        self.lst.delete(0, tk.END)

    def choose_out_dir(self):
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            self.out_dir = Path(d)
            self.lbl_out.config(text=f"Output: {self.out_dir}")

    def process_all(self):
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
    app = App()
    app.mainloop()
