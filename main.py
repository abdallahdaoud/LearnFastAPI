from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, PositiveInt
import sqlite3
# from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allows access from any origin. Restrict this in production!
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

class Employee(BaseModel):
    id: int = None  # Make ID optional for POST requests (auto-increment)
    name: str
    salary: PositiveInt  # Use PositiveInt to enforce positive salary

def setup_database():
    try:
        conn = sqlite3.connect('employees.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                salary INTEGER CHECK (salary > 0)
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise  # Re-raise the exception to stop the application if setup fails

setup_database()

@app.get("/employees/")
async def read_employees():
    try:
        conn = sqlite3.connect('employees.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, salary FROM employees")
        rows = cursor.fetchall()
        conn.close()
        employees = [{"id": row[0], "name": row[1], "salary": row[2]} for row in rows]
        return employees
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch employees")

@app.post("/employees/", status_code=201)
async def create_employee(employee: Employee):
    try:
        conn = sqlite3.connect('employees.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employees (name, salary) VALUES (?, ?)", (employee.name, employee.salary))
        conn.commit()
        employee.id = cursor.lastrowid
        conn.close()
        return employee

    except sqlite3.IntegrityError as e:
         print(f"Database error: {e}")
         raise HTTPException(status_code=400, detail="Invalid salary. Salary must be a positive integer.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create employee")

@app.put("/employees/{employee_id}")
async def update_employee(employee_id: int, employee: Employee):
    try:
        conn = sqlite3.connect('employees.db')
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM employees WHERE id = ?", (employee_id,))
        if cursor.fetchone() is None:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Employee with ID {employee_id} not found")

        cursor.execute("UPDATE employees SET name = ?, salary = ? WHERE id = ?",
                       (employee.name, employee.salary, employee_id))
        if cursor.rowcount == 0:
             conn.close()
             raise HTTPException(status_code=404, detail="Employee not found")
        conn.commit()
        conn.close()
        employee.id = employee_id
        return employee

    except sqlite3.IntegrityError as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=400, detail="Invalid salary. Salary must be a positive integer.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update employee")

@app.delete("/employees/{employee_id}")
async def delete_employee(employee_id: int):
    try:
        conn = sqlite3.connect('employees.db')
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM employees WHERE id = ?", (employee_id,))
        if cursor.fetchone() is None:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Employee with ID {employee_id} not found")

        cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Employee not found")

        conn.commit()
        conn.close()
        return {"message": "Employee deleted successfully"}
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete employee")