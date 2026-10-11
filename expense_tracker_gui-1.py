import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict
import math

# Expense Tracker GUI 2.0
# Keeps the existing expenses.json format and adds dates to new expenses.
DATA_FILE = Path(__file__).with_name("expenses.json")
SETTINGS_FILE = Path(__file__).with_name("settings.json")

BG = "#F4F6FA"
SIDEBAR = "#172033"
CARD = "#FFFFFF"
TEXT = "#202A3B"
MUTED = "#7A8496"
ACCENT = "#4F46E5"
GREEN = "#168A62"
RED = "#D64545"
BORDER = "#E7EAF0"
CHART_COLORS = ["#4F46E5", "#0EA5A4", "#F59E0B", "#E879F9", "#F97316", "#64748B"]


def load_json(path, default):
    """Load JSON without overwriting a user's existing file on read errors."""
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as exc:
        messagebox.showerror(
            "Could not load data",
            f"Couldn't read {path.name}.\nYour file has not been changed.\n\n{exc}"
        )
        return default


def save_json(path, data):
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        return True
    except OSError as exc:
        messagebox.showerror("Save failed", f"Could not save {path.name}:\n{exc}")
        return False


expenses = load_json(DATA_FILE, [])
settings = load_json(SETTINGS_FILE, {"monthly_income": 0.0, "monthly_budget": 0.0})
if not isinstance(expenses, list):
    expenses = []
if not isinstance(settings, dict):
    settings = {"monthly_income": 0.0, "monthly_budget": 0.0}


def money(value):
    return f"₹{value:,.2f}"


def expense_amount(item):
    try:
        return float(item.get("amount", 0))
    except (TypeError, ValueError):
        return 0.0


def expense_month(item):
    value = item.get("date", "")
    return value[:7] if isinstance(value, str) and len(value) >= 7 else ""


class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker | Personal Finance")
        self.root.geometry("1180x760")
        self.root.minsize(980, 650)
        self.root.configure(bg=BG)
        self.current_page = "Dashboard"
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")
        self.month_var = tk.StringVar(value=date.today().strftime("%Y-%m"))
        self.category_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.income_var = tk.StringVar(value=str(settings.get("monthly_income", 0) or 0))
        self.budget_var = tk.StringVar(value=str(settings.get("monthly_budget", 0) or 0))
        self._style()
        self._build_shell()
        self.show_dashboard()

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=CARD, fieldbackground=CARD,
                        foreground=TEXT, rowheight=34, borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#EEF1F7", foreground=TEXT,
                        font=("Segoe UI", 10, "bold"), relief="flat", padding=9)
        style.map("Treeview", background=[("selected", "#E0E7FF")],
                  foreground=[("selected", TEXT)])
        style.configure("TCombobox", padding=7)

    def _build_shell(self):
        self.sidebar = tk.Frame(self.root, bg=SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="◈  MONEYWISE", bg=SIDEBAR, fg="white",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=22, pady=(28, 8))
        tk.Label(self.sidebar, text="PERSONAL FINANCE", bg=SIDEBAR, fg="#AAB4C8",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=24, pady=(0, 28))
        for label, command in [
            ("▦   Dashboard", self.show_dashboard),
            ("☷   Transactions", self.show_transactions),
            ("＋   Add Expense", self.show_add_expense),
            ("◷   Monthly Report", self.show_report),
            ("⚙   Settings", self.show_settings),
        ]:
            btn = tk.Button(self.sidebar, text=label, command=command, anchor="w",
                            bg=SIDEBAR, fg="#E5EAF4", activebackground="#2A3650",
                            activeforeground="white", relief="flat", bd=0,
                            padx=22, pady=13, font=("Segoe UI", 10), cursor="hand2")
            btn.pack(fill="x", padx=10, pady=2)
        tk.Label(self.sidebar, text="Python • JSON • Tkinter", bg=SIDEBAR,
                 fg="#AAB4C8", font=("Segoe UI", 8)).pack(side="bottom", pady=22)

        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self.header = tk.Frame(self.content, bg=BG)
        self.header.pack(fill="x", padx=30, pady=(25, 10))
        self.page_title = tk.Label(self.header, text="", bg=BG, fg=TEXT,
                                   font=("Segoe UI", 23, "bold"))
        self.page_title.pack(side="left")
        self.page_subtitle = tk.Label(self.header, text="", bg=BG, fg=MUTED,
                                      font=("Segoe UI", 10))
        self.page_subtitle.pack(side="left", padx=(15, 0), pady=(10, 0))
        self.body = tk.Frame(self.content, bg=BG)
        self.body.pack(fill="both", expand=True, padx=30, pady=(10, 28))

    def _clear_body(self, title, subtitle=""):
        for widget in self.body.winfo_children():
            widget.destroy()
        self.page_title.config(text=title)
        self.page_subtitle.config(text=subtitle)

    def _card(self, parent, title, value, accent=ACCENT, note=""):
        frame = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        tk.Frame(frame, bg=accent, width=5).pack(side="left", fill="y")
        inside = tk.Frame(frame, bg=CARD)
        inside.pack(side="left", fill="both", expand=True, padx=15, pady=14)
        tk.Label(inside, text=title.upper(), bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(inside, text=value, bg=CARD, fg=TEXT,
                 font=("Segoe UI", 19, "bold")).pack(anchor="w", pady=(7, 2))
        if note:
            tk.Label(inside, text=note, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
        return frame

    def _month_expenses(self, month=None):
        month = month or self.month_var.get()
        return [item for item in expenses if expense_month(item) == month]

    def _safe_amount(self, var, label, allow_zero=False):
        try:
            amount = float(var.get().strip())
            if amount < 0 or (amount == 0 and not allow_zero):
                raise ValueError
            return round(amount, 2)
        except ValueError:
            messagebox.showerror("Invalid amount", f"Enter a valid {label} amount.")
            return None

    def show_dashboard(self):
        self.current_page = "Dashboard"
        self._clear_body("Dashboard", "Your financial snapshot")
        month = date.today().strftime("%Y-%m")
        current = self._month_expenses(month)
        total = sum(expense_amount(item) for item in current)
        income = float(settings.get("monthly_income", 0) or 0)
        budget = float(settings.get("monthly_budget", 0) or 0)
        balance = income - total

        cards = tk.Frame(self.body, bg=BG)
        cards.pack(fill="x")
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1, uniform="cards")
        self._card(cards, "This month's spending", money(total), ACCENT,
                   datetime.now().strftime("%B %Y")).grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._card(cards, "Monthly income", money(income), GREEN,
                   "Set this in Settings").grid(row=0, column=1, sticky="nsew", padx=5)
        self._card(cards, "Remaining balance", money(balance), RED if balance < 0 else GREEN,
                   "Income minus this month's expenses").grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        lower = tk.Frame(self.body, bg=BG)
        lower.pack(fill="both", expand=True, pady=(20, 0))
        lower.grid_columnconfigure(0, weight=3)
        lower.grid_columnconfigure(1, weight=2)
        lower.grid_rowconfigure(0, weight=1)

        recent = tk.Frame(lower, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        recent.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(recent, text="Recent transactions", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(16, 10))
        tree_frame = tk.Frame(recent, bg=CARD)
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        tree = ttk.Treeview(tree_frame, columns=("date", "category", "amount"), show="headings", height=8)
        for col, heading, width in [
            ("date", "DATE", 105), ("category", "CATEGORY", 150), ("amount", "AMOUNT", 110)
        ]:
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        dated = sorted(expenses, key=lambda x: x.get("date", ""), reverse=True)
        for item in dated[:8]:
            tree.insert("", "end", values=(item.get("date", "No date"),
                                           item.get("category", "Other"),
                                           money(expense_amount(item))))

        charts = tk.Frame(lower, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        charts.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        tk.Label(charts, text="Spending by category", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(16, 4))
        chart = tk.Canvas(charts, bg=CARD, height=230, highlightthickness=0)
        chart.pack(fill="both", expand=True, padx=10, pady=5)
        self._draw_pie_chart(chart, current)
        if budget > 0:
            note = f"Budget: {money(budget)}  •  "
            note += f"{money(budget-total)} left" if total <= budget else f"{money(total-budget)} over budget"
            tk.Label(self.body, text=note, bg=BG, fg=RED if total > budget else MUTED,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 0))

    def _draw_pie_chart(self, canvas, items):
        canvas.delete("all")
        totals = defaultdict(float)
        for item in items:
            totals[str(item.get("category", "Other"))] += expense_amount(item)
        data = sorted(totals.items(), key=lambda pair: pair[1], reverse=True)
        if not data or sum(v for _, v in data) <= 0:
            canvas.create_text(140, 90, text="No dated expenses\nfor this month yet",
                               fill=MUTED, font=("Segoe UI", 10), justify="center")
            return
        total = sum(v for _, v in data)
        x0, y0, x1, y1 = 18, 18, 165, 165
        start = 0
        for i, (_, value) in enumerate(data):
            extent = 360 * value / total
            canvas.create_arc(x0, y0, x1, y1, start=start, extent=extent,
                              fill=CHART_COLORS[i % len(CHART_COLORS)], outline=CARD, width=2)
            start += extent
        y = 18
        for i, (category, value) in enumerate(data[:6]):
            canvas.create_rectangle(182, y+3, 193, y+14,
                                    fill=CHART_COLORS[i % len(CHART_COLORS)], outline="")
            label = category if len(category) <= 13 else category[:12] + "…"
            canvas.create_text(201, y+8, text=f"{label}: {money(value)}",
                               anchor="w", fill=TEXT, font=("Segoe UI", 8))
            y += 25

    def show_transactions(self):
        self.current_page = "Transactions"
        self._clear_body("Transactions", "Search, review and remove records")
        top = tk.Frame(self.body, bg=BG)
        top.pack(fill="x", pady=(0, 12))
        tk.Label(top, text="Search category:", bg=BG, fg=TEXT).pack(side="left")
        search = ttk.Entry(top, textvariable=self.search_var, width=25)
        search.pack(side="left", padx=8)
        search.bind("<KeyRelease>", lambda _event: self._refresh_transactions(tree))
        tk.Button(top, text="Delete selected", command=lambda: self._delete_selected(tree),
                  bg="#FEE2E2", fg=RED, relief="flat", padx=12, pady=8,
                  cursor="hand2").pack(side="right")
        frame = tk.Frame(self.body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True)
        cols = ("number", "date", "category", "amount")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col, heading, width in [
            ("number", "#", 55), ("date", "DATE", 150), ("category", "CATEGORY", 280),
            ("amount", "AMOUNT", 150)
        ]:
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="w")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self._refresh_transactions(tree)

    def _refresh_transactions(self, tree):
        tree.delete(*tree.get_children())
        keyword = self.search_var.get().strip().lower()
        for i, item in enumerate(expenses):
            category = str(item.get("category", "Other"))
            if keyword and keyword not in category.lower():
                continue
            tree.insert("", "end", iid=str(i), values=(
                i+1, item.get("date", "Date not recorded"), category,
                money(expense_amount(item))
            ))

    def _delete_selected(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Select an expense", "Select a transaction first.")
            return
        index = int(selected[0])
        item = expenses[index]
        if not messagebox.askyesno("Confirm delete",
                                   f"Delete {item.get('category', 'expense')} — {money(expense_amount(item))}?"):
            return
        del expenses[index]
        if save_json(DATA_FILE, expenses):
            self.show_transactions()

    def show_add_expense(self):
        self.current_page = "Add Expense"
        self._clear_body("Add expense", "Record a new transaction")
        card = tk.Frame(self.body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(anchor="nw", fill="x", padx=0, pady=2)
        form = tk.Frame(card, bg=CARD)
        form.pack(fill="x", padx=24, pady=24)
        form.grid_columnconfigure(1, weight=1)

        def field(row, label, var, hint=None):
            tk.Label(form, text=label, bg=CARD, fg=TEXT,
                     font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w", pady=10)
            entry = ttk.Entry(form, textvariable=var, width=40)
            entry.grid(row=row, column=1, sticky="ew", padx=(20, 0), pady=10, ipady=5)
            if hint:
                tk.Label(form, text=hint, bg=CARD, fg=MUTED,
                         font=("Segoe UI", 9)).grid(row=row+1, column=1, sticky="w", padx=(20, 0))
            return entry

        field(0, "Category", self.category_var, "Example: Food, Travel, Books")
        field(2, "Amount (₹)", self.amount_var)
        field(3, "Date (YYYY-MM-DD)", self.date_var, "Leave today's date or enter a valid date.")
        tk.Button(form, text="＋  Save expense", command=self._add_expense,
                  bg=ACCENT, fg="white", activebackground="#4338CA",
                  activeforeground="white", relief="flat", padx=18, pady=11,
                  font=("Segoe UI", 10, "bold"), cursor="hand2").grid(
                      row=5, column=1, sticky="w", padx=(20, 0), pady=(24, 0))

    def _add_expense(self):
        category = self.category_var.get().strip()
        if not category:
            messagebox.showerror("Missing category", "Enter an expense category.")
            return
        amount = self._safe_amount(self.amount_var, "expense")
        if amount is None:
            return
        raw_date = self.date_var.get().strip()
        try:
            expense_date = datetime.strptime(raw_date, "%Y-%m-%d").date().isoformat()
        except ValueError:
            messagebox.showerror("Invalid date", "Use YYYY-MM-DD, for example 2026-10-10.")
            return
        item = {"category": category.title(), "amount": amount, "date": expense_date}
        expenses.append(item)
        if save_json(DATA_FILE, expenses):
            self.category_var.set("")
            self.amount_var.set("")
            self.date_var.set(date.today().isoformat())
            messagebox.showinfo("Saved", "Expense saved successfully!")
            self.show_dashboard()

    def show_report(self):
        self.current_page = "Monthly Report"
        self._clear_body("Monthly report", "Review spending for a selected month")
        top = tk.Frame(self.body, bg=BG)
        top.pack(fill="x", pady=(0, 14))
        tk.Label(top, text="Month (YYYY-MM)", bg=BG, fg=TEXT).pack(side="left")
        ttk.Entry(top, textvariable=self.month_var, width=14).pack(side="left", padx=10)
        tk.Button(top, text="Generate report", command=self._render_report,
                  bg=ACCENT, fg="white", relief="flat", padx=14, pady=8).pack(side="left")
        self.report_area = tk.Frame(self.body, bg=BG)
        self.report_area.pack(fill="both", expand=True)
        self._render_report()

    def _render_report(self):
        try:
            datetime.strptime(self.month_var.get().strip(), "%Y-%m")
        except ValueError:
            messagebox.showerror("Invalid month", "Enter the month as YYYY-MM, e.g. 2026-10.")
            return
        for widget in self.report_area.winfo_children():
            widget.destroy()
        month = self.month_var.get().strip()
        items = self._month_expenses(month)
        total = sum(expense_amount(item) for item in items)
        income = float(settings.get("monthly_income", 0) or 0)
        budget = float(settings.get("monthly_budget", 0) or 0)
        cards = tk.Frame(self.report_area, bg=BG)
        cards.pack(fill="x")
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1, uniform="report")
        self._card(cards, "Expenses", money(total), ACCENT).grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._card(cards, "Income", money(income), GREEN).grid(row=0, column=1, sticky="nsew", padx=5)
        self._card(cards, "Balance", money(income-total), GREEN if income >= total else RED).grid(
            row=0, column=2, sticky="nsew", padx=(10, 0))
        if budget > 0:
            note_text = f"Budget: {money(budget)}   |   Remaining: {money(budget-total)}"
            if total > budget:
                note_text += "   —  Budget exceeded!"
            tk.Label(self.report_area, text=note_text, bg=BG,
                     fg=RED if total > budget else MUTED,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=15)
        summary = tk.Frame(self.report_area, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        summary.pack(fill="both", expand=True, pady=(15, 0))
        tk.Label(summary, text=f"Category breakdown — {month}", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=14)
        category_totals = defaultdict(float)
        for item in items:
            category_totals[str(item.get("category", "Other"))] += expense_amount(item)
        if not category_totals:
            tk.Label(summary, text="No dated expenses found for this month.",
                     bg=CARD, fg=MUTED).pack(anchor="w", padx=18, pady=10)
        for category, value in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            row = tk.Frame(summary, bg=CARD)
            row.pack(fill="x", padx=18, pady=5)
            tk.Label(row, text=category, bg=CARD, fg=TEXT).pack(side="left")
            tk.Label(row, text=money(value), bg=CARD, fg=TEXT,
                     font=("Segoe UI", 10, "bold")).pack(side="right")

    def show_settings(self):
        self.current_page = "Settings"
        self._clear_body("Settings", "Set income and a monthly spending limit")
        card = tk.Frame(self.body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", anchor="nw")
        form = tk.Frame(card, bg=CARD)
        form.pack(fill="x", padx=24, pady=24)
        form.grid_columnconfigure(1, weight=1)
        for row, label, var in [
            (0, "Monthly income (₹)", self.income_var),
            (1, "Monthly budget (₹)", self.budget_var)
        ]:
            tk.Label(form, text=label, bg=CARD, fg=TEXT,
                     font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w", pady=12)
            ttk.Entry(form, textvariable=var, width=32).grid(
                row=row, column=1, sticky="ew", padx=(22, 0), pady=12, ipady=5)
        tk.Label(form, text="These values are stored in settings.json.",
                 bg=CARD, fg=MUTED).grid(row=2, column=1, sticky="w", padx=(22, 0), pady=(4, 14))
        tk.Button(form, text="Save settings", command=self._save_settings,
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=10,
                  font=("Segoe UI", 10, "bold")).grid(row=3, column=1, sticky="w", padx=(22, 0))

    def _save_settings(self):
        income = self._safe_amount(self.income_var, "income", allow_zero=True)
        if income is None:
            return
        budget = self._safe_amount(self.budget_var, "budget", allow_zero=True)
        if budget is None:
            return
        settings["monthly_income"] = income
        settings["monthly_budget"] = budget
        if save_json(SETTINGS_FILE, settings):
            messagebox.showinfo("Saved", "Income and budget settings saved.")
            self.show_dashboard()


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()
