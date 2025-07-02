
from fastapi import FastAPI, HTTPException, Depends
from typing import List
from database import get_db_connection # Postgres integration
from schemas import ExpenseIn, ExpenseOut
import psycopg2.extras
from fastapi.responses import Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials #Password handling
import secrets
from fastapi.responses import StreamingResponse
import csv #Exporting summary as Excel file
import io
from datetime import datetime #converting to DD-MM-YYYY format
import bcrypt #password hashing
from fastapi.responses import FileResponse 
import matplotlib.pyplot as plt #bar chart
from fastapi.middleware.cors import CORSMiddleware

security = HTTPBasic()

app = FastAPI(
    title="EXPENSE MANAGER",          # appears in swagger UI
    description="Track and manage expenses with user authentication.",
    version="1.0.0"
)
print("🔐 CORS is active: allowing frontend origin")

# ✅ Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://expense-manager-frontend-z5pn.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import FastAPI
from database import get_db_connection

app = FastAPI()

@app.get("/init-db")
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "✅ Users table created successfully"}

        
def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (credentials.username,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            db_password = result[0]
            print("DB password:", db_password)
            print("DB password type:", type(db_password))
            print("User entered password:", credentials.password)

            if bcrypt.checkpw(credentials.password.encode(), db_password if isinstance(db_password, bytes) else db_password.encode()):
                return credentials.username
            else:
                print("Password mismatch")
                raise HTTPException(status_code=401, detail="Incorrect password")
        else:
            print("Username not found")
            raise HTTPException(status_code=401, detail="User not found")

    except HTTPException as he:
        raise he  # Re-raise your expected errors (401)
    except Exception as e:
        print("get_current_user error:", e)
        raise HTTPException(status_code=500, detail="Server error in authentication")


@app.get("/")
def root():
    return {"message": "Welcome to the PostgreSQL Expense Manager API"}

@app.post("/register")
def register_user(username: str, password: str):
    print(f"📥 Register attempt: {username}")
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed.decode()))
        conn.commit()
        cur.close()
        conn.close()

        return {"message": "User registered successfully!"}
    except Exception as e:
        print("❌ Registration error:", e)
        raise HTTPException(status_code=500, detail=str(e))

    

@app.post("/login")
def login(current_user: str = Depends(get_current_user)):
    return {"message": f"Welcome, {current_user}!"}


@app.post("/add", response_model=dict)
def add_expense(expense: ExpenseIn, current_user: str = Depends(get_current_user)):
    # Convert DD-MM-YYYY to datetime.date
    # Convert ISO (YYYY-MM-DD) string to datetime.date
    try:
        print("Received date:", expense.date)
        date_obj = datetime.strptime(expense.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Date format must be YYYY-MM-DD")


    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if expense.amount < 0 or expense.amount > 99999999:
            raise HTTPException(status_code=400, detail="Invalid amount range.")

        cur.execute(
            """
            INSERT INTO expenses (username, reason, amount, date)
            VALUES (%s, %s, %s, %s)
            """,
            (current_user, expense.reason, expense.amount, date_obj)
        )
        conn.commit()

        return {
            "message": "Expense added successfully",
            "data": {
                "username": current_user,
                "reason": expense.reason,
                "amount": expense.amount,
                "date": expense.date
            }
        }
    except Exception as e:
        conn.rollback()
        print("ADD ERROR:", e)  # ADD THIS
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()



@app.get("/expenses", response_model=List[ExpenseOut])
def get_expenses(current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute(
        "SELECT sno, username, reason, amount, date FROM expenses WHERE LOWER(username) = LOWER(%s)",
        (current_user,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No expenses found.")

    return [ExpenseOut(**dict(row)) for row in rows]



@app.get("/search/", response_model=List[ExpenseOut])
def search_by_reason(reason: str, current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        "SELECT sno, username, reason, amount, date FROM expenses WHERE LOWER(reason) = LOWER(%s) AND LOWER(username) = LOWER(%s)",
        (reason, current_user)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No matching expenses.")
    
    return [ExpenseOut(**dict(row)) for row in rows]


@app.get("/search/date", response_model=List[ExpenseOut])
def search_by_date(date: str, current_user: str = Depends(get_current_user)):
    try:
        # Parse the correct format: YYYY-MM-DD
        search_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Date format should be YYYY-MM-DD")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """
        SELECT sno, username, reason, amount, date
        FROM expenses
        WHERE username = %s AND date = %s
        """,
        (current_user, search_date)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No expenses found on this date.")

    return [ExpenseOut(**dict(row)) for row in rows]

@app.delete("/delete/", response_model=dict)
def delete_by_reason(reason: str, current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM expenses WHERE LOWER(reason) = LOWER(%s) AND LOWER(username) = LOWER(%s)",
        (reason, current_user)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"message": f"Deleted all expenses for reason: {reason}"}

@app.delete("/delete/sno/{sno}", response_model=dict)
def delete_by_sno(sno: int, current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure the expense belongs to the current user
    cur.execute("SELECT * FROM expenses WHERE sno = %s AND username = %s", (sno, current_user))
    result = cur.fetchone()
    if not result:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Expense not found or does not belong to user.")

    cur.execute("DELETE FROM expenses WHERE sno = %s", (sno,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": f"Deleted expense with sno: {sno}"}


@app.get("/summary", response_model=dict)
def get_summary(current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT amount, date
            FROM expenses
            WHERE LOWER(username) = LOWER(%s)
            """,
            (current_user,)
        )
        rows = cur.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No expenses found.")

        amounts = [row[0] for row in rows]
        total = sum(amounts)
        average = total / len(amounts)
        highest = max(amounts)
        lowest = min(amounts)

        # Find the dates for highest and lowest
        highest_date = next(row[1] for row in rows if row[0] == highest)
        lowest_date = next(row[1] for row in rows if row[0] == lowest)

        return {
            "username": current_user,
            "total_expense": round(total, 2),
            "average_expense": round(average, 2),
            "highest_expense": round(highest, 2),
            "highest_date": highest_date.strftime("%d-%m-%Y"),
            "lowest_expense": round(lowest, 2),
            "lowest_date": lowest_date.strftime("%d-%m-%Y"),
            "records": len(amounts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()



@app.get("/summary/monthly", response_model=dict)
def get_monthly_summary(month: int, year: int, current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT amount FROM expenses 
            WHERE username = %s AND EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s
            """,
            (current_user, month, year)
        )
        rows = cur.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No expenses found for given month/year.")

        amounts = [row[0] for row in rows]
        total = sum(amounts)
        average = total / len(amounts)
        highest = max(amounts)
        lowest = min(amounts)

        return {
            "month": f"{month:02d}-{year}",
            "total": total,
            "average": average,
            "highest": highest,
            "lowest": lowest,
            "count": len(amounts)
        }
    finally:
        cur.close()
        conn.close()


# CSV Export Route
@app.get("/export/csv")
def export_csv(current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT sno, username, reason, amount, date FROM expenses WHERE LOWER(username) = LOWER(%s)", (current_user,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No expenses found")

    # Create in-memory CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["S.No", "Username", "Reason", "Amount", "Date"])
    for row in rows:
        sno, username, reason, amount, date = row
        formatted_date = date.strftime("%d-%m-%Y")
        writer.writerow([sno, username, reason, amount, formatted_date])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={current_user}_expenses.csv"
    return response

#Bar Chart Export
from fastapi.responses import StreamingResponse
import matplotlib.pyplot as plt
from io import BytesIO

@app.get("/export/bar-chart")
def export_bar_chart(current_user: str = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT reason, SUM(amount)
        FROM expenses
        WHERE username = %s
        GROUP BY reason
        ORDER BY SUM(amount) DESC
    """, (current_user,))
    data = cur.fetchall()
    cur.close()
    conn.close()

    if not data:
        raise HTTPException(status_code=404, detail="No expense data available")

    reasons = [row[0] for row in data]
    amounts = [row[1] for row in data]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(reasons, amounts, color='skyblue')
    plt.title(f"Expenses by Reason - {current_user}")
    plt.xlabel("Reason")
    plt.ylabel("Total Amount (₹)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    for bar, amt in zip(bars, amounts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"₹{amt:.2f}", ha='center', va='bottom', fontsize=8)

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


