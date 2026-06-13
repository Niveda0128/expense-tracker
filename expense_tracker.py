import json

# ---------------- LOAD EXPENSES ----------------
def load_expenses():
    try:
        with open("expenses.json", "r") as file:
            return json.load(file)
    except:
        return []

# ---------------- SAVE EXPENSES ----------------
def save_expenses():
    with open("expenses.json", "w") as file:
        json.dump(expenses, file, indent=4)

# Load data at start
expenses = load_expenses()

# ---------------- ADD EXPENSE ----------------
def add_expense():
    category = input("Enter category: ")
    amount = float(input("Enter amount: "))

    expense = {
        "category": category,
        "amount": amount
    }

    expenses.append(expense)
    save_expenses()
    print("Expense Added Successfully!")

# ---------------- VIEW EXPENSES ----------------
def view_expenses():
    if not expenses:
        print("No expenses found")
        return

    print("\n--- EXPENSE LIST ---")
    for i, e in enumerate(expenses):
        print(f"{i}. {e['category']} - {e['amount']}")

# ---------------- DELETE EXPENSE ----------------
def delete_expense():
    view_expenses()

    if not expenses:
        return

    try:
        index = int(input("Enter index to delete: "))

        if 0 <= index < len(expenses):
            removed = expenses.pop(index)
            save_expenses()
            print("Deleted:", removed)
        else:
            print("Invalid index")

    except:
        print("Please enter valid number")

# ---------------- TOTAL EXPENSE ----------------
def total_expense():
    total = sum(e["amount"] for e in expenses)
    print("\nTotal Expense:", total)

# ---------------- SEARCH EXPENSE ----------------
def search_expense():
    keyword = input("Enter category to search: ").lower()

    found = False

    for e in expenses:
        if keyword in e["category"].lower():
            print(e["category"], "-", e["amount"])
            found = True

    if not found:
        print("No matching expenses found")

# ---------------- CATEGORY TOTAL ----------------
def category_total():
    totals = {}

    for e in expenses:
        cat = e["category"]

        if cat in totals:
            totals[cat] += e["amount"]
        else:
            totals[cat] = e["amount"]

    print("\n--- CATEGORY TOTAL ---")
    for k, v in totals.items():
        print(k, "-", v)

# ---------------- MAIN MENU ----------------
while True:
    print("\n====== EXPENSE TRACKER ======")
    print("1. Add Expense")
    print("2. View Expenses")
    print("3. Delete Expense")
    print("4. Show Total Expense")
    print("5. Search Expense")
    print("6. Category-wise Total")
    print("7. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        add_expense()

    elif choice == "2":
        view_expenses()

    elif choice == "3":
        delete_expense()

    elif choice == "4":
        total_expense()

    elif choice == "5":
        search_expense()

    elif choice == "6":
        category_total()

    elif choice == "7":
        print("Goodbye!")
        break

    else:
        print("Invalid choice")
