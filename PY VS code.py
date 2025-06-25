from prettytable import PrettyTable
from datetime import datetime
import psycopg2

class expense_manager(): 
    def __init__(self):
        # connect to PostgreSQL
        self.conn = psycopg2.connect(
            dbname="expense manager final",
            user="postgres",
            password="Sahana@2006",  # CHANGE THIS
            host="localhost",
            port="5432"
        )
        self.cur = self.conn.cursor()
        self.username = None

    def input_expense(self):
        self.username = input("Enter your name: ").strip()
        if not self.username:
            print("Name cannot be empty!")
            return

        print("\nEnter your expenses.\nType 'Complete' to get the summary.\n")
        count = 0
        while True:
            reason = input("Enter reason (or 'complete' to end): ")
            if reason.lower() == 'complete':
                if count == 0:
                    print("No data entered.")
                else:
                    print("Data added successfully.")
                break

            if not reason.replace(" ", "").isalpha():
                print("Please enter only letters for reason.\n")
                continue
            if len(reason) > 30:
                print("Reason is too long! Please keep it under 30 characters.\n")
                continue

            try:
                amount_input = input("Enter amount: ₹")
                amount = float(amount_input)

                parts = amount_input.split(".")
                before_decimal = parts[0]
                after_decimal = parts[1] if len(parts) > 1 else ""

                if len(before_decimal) > 8:
                    print("Amount too large! Maximum 8 digits before decimal allowed.\n")
                    continue

                if len(after_decimal) > 5:
                    print("Only 5 digits allowed after decimal.\n")
                    continue

                if amount < 0:
                    print("Amount cannot be negative.\n")
                    continue

            except ValueError:
                print("Please enter a valid number.\n")
                continue

            try:
                date_str = input("Enter date (DD/MM/YYYY): ")
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            except ValueError:
                print("Invalid date format. Please enter in DD/MM/YYYY format.\n")
                continue

            self.cur.execute(
                "INSERT INTO expenses (username, reason, amount, date) VALUES (%s, %s, %s, %s)",
                (self.username, reason, amount, date_obj)
            )

            self.conn.commit()
            count += 1
            print("Saved successfully!\n")

    def display_summary(self):
        self.cur.execute("SELECT * FROM expenses WHERE username = %s", (self.username,))
        rows = self.cur.fetchall()

        if not rows:
            print("No expenses found.")
            return

        total = 0
        amounts = []
        table = PrettyTable()
        table.field_names = ["S.No.","Username", "Reason", "Amount", "Date"]

        for i, row in enumerate(rows):
            expense_id, username,reason, amount, date = row

            table.add_row([i + 1, self.username,reason, f"₹{float(amount):.2f}", date.strftime("%d/%m/%Y")])
            amounts.append(amount)
            total += amount

        average = total / len(amounts)
        highest = max(amounts)
        lowest = min(amounts)

        print("\n----------- EXPENSE SUMMARY ----------")
        print(table)
        print(f"\nTotal Expense: ₹{total:.2f}")
        print(f"Average Expense: ₹{average:.2f}")
        print(f"Highest Expense: ₹{highest:.2f}")
        print(f"Lowest Expense: ₹{lowest:.2f}")

    def search_by_reason(self, keyword):
        self.cur.execute(
            "SELECT * FROM expenses WHERE LOWER(reason) = LOWER(%s) AND username = %s",
            (keyword, self.username)
        )
        rows = self.cur.fetchall()

        if not rows:
            print(f"No expenses found for reason '{keyword}'.")
            return

        total = 0
        table = PrettyTable()
        table.field_names = ["S.No.","Username", "Reason", "Amount", "Date"]

        for i, row in enumerate(rows):
            expense_id, username,reason, amount, date = row
            table.add_row([i + 1, self.username, reason, f"₹{float(amount):.2f}", date.strftime("%d/%m/%Y")])
            total += amount

        print(f"\nExpenses related to '{keyword}':")
        print(table)
        print(f"\nTotal spent on '{keyword}': ₹{total:.2f}")

    def search_by_date_range(self, start_date, end_date):
        try:
            start = datetime.strptime(start_date, "%d/%m/%Y").date()
            end = datetime.strptime(end_date, "%d/%m/%Y").date()
        except ValueError:
            print("Invalid date format. Please use DD/MM/YYYY.")
            return

        self.cur.execute(
            "SELECT * FROM expenses WHERE date BETWEEN %s AND %s AND username = %s ORDER BY date",
            (start, end, self.username)
        )
        rows = self.cur.fetchall()

        if not rows:
            print("No expenses found in the given date range.")
            return

        total = 0
        table = PrettyTable()
        table.field_names = ["S.No.", "Username","Reason", "Amount", "Date"]

        for i, row in enumerate(rows):
            expense_id, username,reason, amount, date = row
            table.add_row([i + 1,self.username, reason, f"₹{amount:.2f}", date.strftime("%d/%m/%Y")])
            total += amount

        print(f"\nExpenses from {start_date} to {end_date}:")
        print(table)
        print(f"\nTotal spent between {start_date} and {end_date}: ₹{total:.2f}")

    def delete_by_reason(self, reason):
        self.cur.execute(
            "DELETE FROM expenses WHERE LOWER(reason) = LOWER(%s) AND username = %s",
            (reason, self.username)
        )
        self.conn.commit()
        print(f"Deleted all expenses with reason '{reason}'.")

    def delete_all(self):
        self.cur.execute("DELETE FROM expenses WHERE username = %s", (self.username,))
        self.conn.commit()
        print("All your expenses deleted!")

    def close(self):
        self.cur.close()
        self.conn.close()

# Main program
manager = expense_manager()

while True:
    print("\n----- EXPENSE MANAGER MENU -----")
    print("1. Add Expense")
    print("2. Show Summary")
    print("3. Search by Reason")
    print("4. Search by Date Range")
    print("5. Delete by Reason")
    print("6. Delete All")
    print("7. Exit")

    choice = input("Enter your choice (1-7): ")

    if choice == "1":
        manager.input_expense()
    elif choice == "2":
        manager.display_summary()
    elif choice == "3":
        keyword = input("Enter reason to search: ")
        manager.search_by_reason(keyword)
    elif choice == "4":
        start = input("Enter start date (DD/MM/YYYY): ")
        end = input("Enter end date (DD/MM/YYYY): ")
        manager.search_by_date_range(start, end)
    elif choice == "5":
        reason = input("Enter reason to delete: ")
        manager.delete_by_reason(reason)
    elif choice == "6":
        confirm = input("Are you sure you want to delete ALL your expenses? (yes/no): ")
        if confirm.lower() == "yes":
            manager.delete_all()
    elif choice == "7":
        print("Thank You!")
        manager.close()
        break
    else:
        print("Invalid choice. Please enter a number from 1 to 7.")
