"""
Travel Planner - Python Desktop Application (Tkinter)

Syllabus concepts used (look for the [SYLLABUS n] tags in the comments):
  1. Data structures and functions : dictionaries, lists, modular functions
  2. File handling                 : pickle / csv / txt with the 'with' statement
  3. Exception handling            : try-except-else-finally, custom exceptions
  4. GUI design                    : Tkinter widgets, menu bar, Notebook tabs

Run with:  python travel_planner.py
"""

import csv
import pickle
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

CURRENCY = "₹"
STYLES = ["Leisure", "Adventure", "Business", "Family", "Budget"]
BOOKING_TYPES = ["Flight", "Train", "Bus", "Hotel", "Activity"]
BOOKING_STATUS = ["Confirmed", "Pending", "Cancelled"]
EXPENSE_CATEGORIES = ["Food", "Transport", "Shopping", "Sightseeing", "Other"]


# ======================================================================
# [SYLLABUS 3] CUSTOM EXCEPTIONS
# A base exception plus two specific ones, so callers can catch them
# individually or together.
# ======================================================================
class TravelPlannerError(Exception):
    """Base class for every error raised by this application."""


class InvalidInputError(TravelPlannerError):
    """Raised when the user types something unacceptable in a form."""


class DataFormatError(TravelPlannerError):
    """Raised when a loaded file does not contain a valid travel plan."""


# ======================================================================
# [SYLLABUS 1] DATA STRUCTURES AND FUNCTIONS
# The whole trip is ONE dictionary. Its values are strings, numbers,
# a nested dictionary (preferences) and lists of dictionaries.
# ======================================================================
def new_plan():
    """Return an empty travel plan (dict)."""
    return {
        "trip_name": "",
        "budget_limit": 0.0,
        "preferences": {"style": STYLES[0], "transport": "Flight",
                        "hotel": True, "insurance": False},
        "destinations": [],   # list of dicts: name, days, cost_per_day, activities
        "bookings": [],       # list of dicts: type, destination, amount, status
        "expenses": [],       # list of dicts: category, description, amount
    }


def require_text(text, field):
    """Return stripped text or raise InvalidInputError if it is empty."""
    text = text.strip()
    if not text:
        raise InvalidInputError(f"{field} cannot be empty.")
    return text


def parse_number(text, field, minimum=0):
    """
    Convert text to float. Demonstrates try-except-else:
    the else block runs only when conversion succeeded.
    """
    try:
        value = float(text.strip())
    except ValueError:
        raise InvalidInputError(f"{field} must be a number.")
    else:
        if value < minimum:
            raise InvalidInputError(f"{field} must be at least {minimum}.")
        return value


def destination_cost(dest):
    """Estimated cost of one destination = days x cost per day."""
    return dest["days"] * dest["cost_per_day"]


def calculate_budget(plan):
    """Return a dictionary summarising the trip budget."""
    stay = sum(destination_cost(d) for d in plan["destinations"])
    # Cancelled bookings are not counted
    bookings = sum(b["amount"] for b in plan["bookings"]
                   if b["status"] != "Cancelled")
    expenses = sum(e["amount"] for e in plan["expenses"])
    total = stay + bookings + expenses
    return {"stay": stay, "bookings": bookings, "expenses": expenses,
            "total": total, "limit": plan["budget_limit"],
            "remaining": plan["budget_limit"] - total}


def format_budget(summary):
    """Turn the budget dictionary into readable text."""
    lines = [
        "BUDGET SUMMARY",
        "-" * 40,
        f"Destination estimates : {CURRENCY}{summary['stay']:.2f}",
        f"Bookings (active)     : {CURRENCY}{summary['bookings']:.2f}",
        f"Expenses              : {CURRENCY}{summary['expenses']:.2f}",
        f"TOTAL                 : {CURRENCY}{summary['total']:.2f}",
        f"Budget limit          : {CURRENCY}{summary['limit']:.2f}",
        f"Remaining             : {CURRENCY}{summary['remaining']:.2f}",
    ]
    if summary["limit"] > 0:
        lines.append("STATUS: WITHIN BUDGET" if summary["remaining"] >= 0
                     else "STATUS: OVER BUDGET!")
    return "\n".join(lines)


def build_itinerary_text(plan):
    """Build a day-wise itinerary string from the plan."""
    prefs = plan["preferences"]
    lines = [
        f"TRIP: {plan['trip_name'] or 'Untitled Trip'}",
        f"Style: {prefs['style']} | Transport: {prefs['transport']}",
        f"Hotel needed: {'Yes' if prefs['hotel'] else 'No'} | "
        f"Insurance: {'Yes' if prefs['insurance'] else 'No'}",
        "-" * 40,
    ]
    if not plan["destinations"]:
        lines.append("No destinations added yet.")
    day = 1
    for dest in plan["destinations"]:
        last_day = day + dest["days"] - 1
        lines.append(f"Day {day}-{last_day}: {dest['name']} "
                     f"({dest['days']} days)")
        if dest["activities"]:
            lines.append(f"    Activities: {dest['activities']}")
        day = last_day + 1
    return "\n".join(lines)


# ======================================================================
# [SYLLABUS 2] FILE HANDLING - every file is opened with 'with'
# ======================================================================
def validate_plan(plan):
    """Check that loaded data has the structure of a travel plan."""
    required = {"trip_name", "budget_limit", "preferences",
                "destinations", "bookings", "expenses"}
    if not isinstance(plan, dict) or not required.issubset(plan):
        raise DataFormatError("File is not a valid Travel Planner plan.")
    for key in ("destinations", "bookings", "expenses"):
        if not isinstance(plan[key], list):
            raise DataFormatError(f"'{key}' data is corrupted.")


def save_plan(plan, path):
    """Save the whole plan to a binary file using pickle."""
    try:
        with open(path, "wb") as file:
            pickle.dump(plan, file)
    except OSError as err:
        raise TravelPlannerError(f"Could not save file: {err}")
    finally:
        # finally always runs, whether saving worked or not
        print(f"[log] save attempted: {path}")


def load_plan(path):
    """Load a plan from a pickle file and validate it."""
    try:
        with open(path, "rb") as file:
            plan = pickle.load(file)
    except FileNotFoundError:
        raise TravelPlannerError("File not found.")
    except (pickle.UnpicklingError, EOFError, AttributeError,
            ImportError, IndexError):
        raise DataFormatError("File is empty or not a Travel Planner file.")
    except OSError as err:
        raise TravelPlannerError(f"Could not read file: {err}")
    else:
        validate_plan(plan)
        return plan
    finally:
        print(f"[log] load attempted: {path}")


def export_csv(plan, path):
    """Export destinations to a CSV file (opens in Excel)."""
    try:
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Destination", "Days", "Cost per day",
                             "Total", "Activities"])
            for d in plan["destinations"]:
                writer.writerow([d["name"], d["days"], d["cost_per_day"],
                                 destination_cost(d), d["activities"]])
    except OSError as err:
        raise TravelPlannerError(f"Could not export CSV: {err}")


def export_report(plan, path):
    """Write itinerary + budget as a plain text report."""
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(build_itinerary_text(plan) + "\n\n")
            file.write(format_budget(calculate_budget(plan)) + "\n")
    except OSError as err:
        raise TravelPlannerError(f"Could not export report: {err}")


# ======================================================================
# [SYLLABUS 4] GUI DESIGN USING TKINTER
# ======================================================================
def fmt_destination(d):
    return (f"{d['name']} | {d['days']} days | "
            f"{CURRENCY}{d['cost_per_day']:.0f}/day | {d['activities']}")


def fmt_booking(b):
    return (f"{b['type']} | {b['destination'] or '-'} | "
            f"{CURRENCY}{b['amount']:.0f} | {b['status']}")


def fmt_expense(e):
    return f"{e['category']} | {e['description']} | {CURRENCY}{e['amount']:.0f}"


class TravelPlannerApp:
    """Main window of the application."""

    def __init__(self, root):
        self.root = root
        self.root.title("Travel Planner")
        self.root.geometry("860x660")
        self.plan = new_plan()
        self.current_file = None

        # Tkinter variables linked to widgets
        self.trip_var = tk.StringVar()
        self.style_var = tk.StringVar(value=STYLES[0])
        self.transport_var = tk.StringVar(value="Flight")   # Radiobuttons
        self.hotel_var = tk.BooleanVar(value=True)          # Checkbuttons
        self.insurance_var = tk.BooleanVar(value=False)
        self.budget_var = tk.StringVar()

        # One dictionary holds all the form field variables
        keys = ["dest_name", "dest_days", "dest_cost", "dest_acts",
                "book_type", "book_dest", "book_amount", "book_status",
                "exp_cat", "exp_desc", "exp_amount"]
        self.f = {key: tk.StringVar() for key in keys}
        self.widgets = {}

        self.build_menu()
        self.build_top_panel()
        self.build_tabs()
        self.status = ttk.Label(self.root, text="Ready", relief="sunken",
                                anchor="w")
        self.status.pack(fill="x", side="bottom")
        self.refresh()
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    # ---------------- Menu bar ----------------
    def build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Plan", command=self.new_file)
        file_menu.add_command(label="Open Plan...", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        export_menu = tk.Menu(menubar, tearoff=0)
        export_menu.add_command(label="Export Itinerary (CSV)",
                                command=self.do_export_csv)
        export_menu.add_command(label="Export Report (TXT)",
                                command=self.do_export_report)
        menubar.add_cascade(label="Export", menu=export_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(
            "About", "Travel Planner\nPlan trips, track budgets, save plans."))
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

    # ---------------- Trip details and preferences ----------------
    def build_top_panel(self):
        frame = ttk.LabelFrame(self.root, text="Trip Details and Preferences",
                               padding=8)
        frame.pack(fill="x", padx=8, pady=6)

        ttk.Label(frame, text="Trip name:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.trip_var, width=28).grid(
            row=0, column=1, padx=4)
        ttk.Label(frame, text="Style:").grid(row=0, column=2, sticky="e")
        ttk.Combobox(frame, textvariable=self.style_var, values=STYLES,
                     state="readonly", width=12).grid(row=0, column=3, padx=4)
        ttk.Label(frame, text=f"Budget ({CURRENCY}):").grid(
            row=0, column=4, sticky="e")
        ttk.Entry(frame, textvariable=self.budget_var, width=12).grid(
            row=0, column=5, padx=4)

        ttk.Label(frame, text="Transport:").grid(row=1, column=0, sticky="w")
        radio_frame = ttk.Frame(frame)
        radio_frame.grid(row=1, column=1, columnspan=2, sticky="w")
        for mode in ("Flight", "Train", "Road"):
            ttk.Radiobutton(radio_frame, text=mode, value=mode,
                            variable=self.transport_var).pack(side="left")
        ttk.Checkbutton(frame, text="Hotel needed",
                        variable=self.hotel_var).grid(row=1, column=3)
        ttk.Checkbutton(frame, text="Travel insurance",
                        variable=self.insurance_var).grid(
            row=1, column=4, columnspan=2)

    # ---------------- Tabs ----------------
    def build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=4)

        self.dest_list = self.build_tab(
            "Destinations",
            [("Destination", "dest_name", None),
             ("Days", "dest_days", None),
             (f"Cost per day ({CURRENCY})", "dest_cost", None),
             ("Activities", "dest_acts", None)],
            self.add_destination, "destinations")
        self.book_list = self.build_tab(
            "Bookings",
            [("Type", "book_type", BOOKING_TYPES),
             ("Destination", "book_dest", []),
             (f"Amount ({CURRENCY})", "book_amount", None),
             ("Status", "book_status", BOOKING_STATUS)],
            self.add_booking, "bookings")
        self.exp_list = self.build_tab(
            "Expenses",
            [("Category", "exp_cat", EXPENSE_CATEGORIES),
             ("Description", "exp_desc", None),
             (f"Amount ({CURRENCY})", "exp_amount", None)],
            self.add_expense, "expenses")
        self.build_summary_tab()

        # (listbox, plan key, formatter) used by refresh()
        self.list_specs = [(self.dest_list, "destinations", fmt_destination),
                           (self.book_list, "bookings", fmt_booking),
                           (self.exp_list, "expenses", fmt_expense)]

    def build_tab(self, title, fields, add_command, plan_key):
        """Create one tab with a form, Add/Remove buttons and a Listbox."""
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text=title)
        form = ttk.Frame(tab)
        form.pack(fill="x")

        for row, (label, key, values) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row, column=0,
                                             sticky="w", pady=2)
            if values is None:
                widget = ttk.Entry(form, textvariable=self.f[key], width=45)
            else:
                widget = ttk.Combobox(form, textvariable=self.f[key],
                                      values=values, state="readonly",
                                      width=42)
                if values:
                    self.f[key].set(values[0])
            widget.grid(row=row, column=1, padx=6, pady=2, sticky="w")
            self.widgets[key] = widget

        listbox_holder = ttk.Frame(tab)
        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", pady=6)
        listbox_holder.pack(fill="both", expand=True)

        listbox = tk.Listbox(listbox_holder, height=10)
        scroll = ttk.Scrollbar(listbox_holder, command=listbox.yview)
        listbox.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        listbox.pack(fill="both", expand=True)

        ttk.Button(buttons, text="Add", command=add_command).pack(side="left")
        ttk.Button(buttons, text="Remove Selected",
                   command=lambda: self.remove_selected(listbox, plan_key)
                   ).pack(side="left", padx=6)
        return listbox

    def build_summary_tab(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="Itinerary and Budget")
        buttons = ttk.Frame(tab)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Show Itinerary",
                   command=self.show_itinerary).pack(side="left")
        ttk.Button(buttons, text="Calculate Budget",
                   command=self.show_budget).pack(side="left", padx=6)

        holder = ttk.Frame(tab)
        holder.pack(fill="both", expand=True, pady=6)
        self.output = tk.Text(holder, height=16, state="disabled",
                              font=("Courier New", 10))
        scroll = ttk.Scrollbar(holder, command=self.output.yview)
        self.output.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.output.pack(fill="both", expand=True)

    # ---------------- Add / remove actions ----------------
    def add_destination(self):
        try:
            name = require_text(self.f["dest_name"].get(), "Destination")
            days = int(parse_number(self.f["dest_days"].get(), "Days",
                                    minimum=1))
            cost = parse_number(self.f["dest_cost"].get(), "Cost per day")
        except InvalidInputError as err:
            messagebox.showwarning("Invalid input", str(err))
        else:
            self.plan["destinations"].append({
                "name": name, "days": days, "cost_per_day": cost,
                "activities": self.f["dest_acts"].get().strip()})
            self.clear("dest_name", "dest_days", "dest_cost", "dest_acts")
            self.refresh()

    def add_booking(self):
        try:
            amount = parse_number(self.f["book_amount"].get(), "Amount")
        except InvalidInputError as err:
            messagebox.showwarning("Invalid input", str(err))
        else:
            self.plan["bookings"].append({
                "type": self.f["book_type"].get(),
                "destination": self.f["book_dest"].get(),
                "amount": amount, "status": self.f["book_status"].get()})
            self.clear("book_amount")
            self.refresh()

    def add_expense(self):
        try:
            description = require_text(self.f["exp_desc"].get(), "Description")
            amount = parse_number(self.f["exp_amount"].get(), "Amount")
        except InvalidInputError as err:
            messagebox.showwarning("Invalid input", str(err))
        else:
            self.plan["expenses"].append({
                "category": self.f["exp_cat"].get(),
                "description": description, "amount": amount})
            self.clear("exp_desc", "exp_amount")
            self.refresh()

    def remove_selected(self, listbox, plan_key):
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Remove", "Please select an item first.")
            return
        del self.plan[plan_key][selection[0]]
        self.refresh()

    def clear(self, *keys):
        for key in keys:
            self.f[key].set("")

    # ---------------- Keeping plan and screen in sync ----------------
    def refresh(self):
        """Redraw all three listboxes from the plan data."""
        for listbox, key, formatter in self.list_specs:
            listbox.delete(0, tk.END)
            for item in self.plan[key]:
                listbox.insert(tk.END, formatter(item))
        names = [d["name"] for d in self.plan["destinations"]]
        self.widgets["book_dest"]["values"] = names
        if self.f["book_dest"].get() not in names:
            self.f["book_dest"].set(names[0] if names else "")

    def sync_plan_from_ui(self):
        """Copy top-panel widget values into the plan dictionary."""
        self.plan["trip_name"] = self.trip_var.get().strip()
        self.plan["budget_limit"] = parse_number(
            self.budget_var.get().strip() or "0", "Budget")
        self.plan["preferences"] = {
            "style": self.style_var.get(),
            "transport": self.transport_var.get(),
            "hotel": self.hotel_var.get(),
            "insurance": self.insurance_var.get()}

    def load_ui_from_plan(self):
        """Fill top-panel widgets from the plan dictionary."""
        prefs = self.plan["preferences"]
        self.trip_var.set(self.plan["trip_name"])
        self.budget_var.set(str(self.plan["budget_limit"]))
        self.style_var.set(prefs.get("style", STYLES[0]))
        self.transport_var.set(prefs.get("transport", "Flight"))
        self.hotel_var.set(prefs.get("hotel", True))
        self.insurance_var.set(prefs.get("insurance", False))
        self.refresh()

    def set_output(self, text):
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.config(state="disabled")

    def show_itinerary(self):
        try:
            self.sync_plan_from_ui()
        except InvalidInputError as err:
            messagebox.showwarning("Invalid input", str(err))
        else:
            self.set_output(build_itinerary_text(self.plan))

    def show_budget(self):
        try:
            self.sync_plan_from_ui()
        except InvalidInputError as err:
            messagebox.showwarning("Invalid input", str(err))
        else:
            self.set_output(format_budget(calculate_budget(self.plan)))

    # ---------------- File menu actions ----------------
    def new_file(self):
        if messagebox.askyesno("New Plan", "Discard the current plan?"):
            self.plan = new_plan()
            self.current_file = None
            self.load_ui_from_plan()
            self.set_output("")
            self.status.config(text="New plan created")

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Travel plans", "*.dat"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.plan = load_plan(path)
        except TravelPlannerError as err:
            messagebox.showerror("Load failed", str(err))
        else:
            self.current_file = path
            self.load_ui_from_plan()
            self.status.config(text=f"Loaded {path}")

    def save_file(self):
        if self.current_file:
            self.write_to(self.current_file)
        else:
            self.save_as()

    def save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".dat",
            filetypes=[("Travel plans", "*.dat")])
        if path:
            self.write_to(path)

    def write_to(self, path):
        try:
            self.sync_plan_from_ui()
            save_plan(self.plan, path)
        except TravelPlannerError as err:
            messagebox.showerror("Save failed", str(err))
        else:
            self.current_file = path
            self.status.config(text=f"Saved {path}")

    def do_export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if path:
            try:
                export_csv(self.plan, path)
            except TravelPlannerError as err:
                messagebox.showerror("Export failed", str(err))
            else:
                self.status.config(text=f"Exported {path}")

    def do_export_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text", "*.txt")])
        if path:
            try:
                self.sync_plan_from_ui()
                export_report(self.plan, path)
            except TravelPlannerError as err:
                messagebox.showerror("Export failed", str(err))
            else:
                self.status.config(text=f"Exported {path}")

    def exit_app(self):
        if messagebox.askyesno("Exit", "Quit Travel Planner?"):
            self.root.destroy()


def main():
    root = tk.Tk()
    TravelPlannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
