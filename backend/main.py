import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel # <-- NEO ERGALEIO

app = FastAPI(title="ENTERSOFTONE B2B Integration API")

# --- TO SETUP TIS VASES POU EIXAME ---
def init_db():
    conn = sqlite3.connect('erp_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commercial_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            total_amount REAL NOT NULL,
            document_type TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 1. NEO KOMMATI: To Montelo Dedomenwn (Schema) ---
class InvoicePayload(BaseModel):
    document_number: str
    customer_name: str
    total_amount: float

# --- 2. NEO KOMMATI: H POST Porta pou dexetai ta dedomena ---
@app.post("/api/invoices")
def create_invoice(invoice: InvoicePayload):
    try:
        # Anoigoume tin porta tou xrimatokivwtiou
        conn = sqlite3.connect('erp_system.db')
        cursor = conn.cursor()

        # Apothikeuoume ta dedomena. Ta '?' einai poly simantika!
        cursor.execute('''
            INSERT INTO commercial_documents 
            (document_number, customer_name, total_amount, document_type, status)
            VALUES (?, ?, ?, 'Invoice', 'Pending')
        ''', (invoice.document_number, invoice.customer_name, invoice.total_amount))

        # Kleinoume me asfaleia
        conn.commit()
        conn.close()

        return {"status": "success", "message": f"To timologio {invoice.document_number} perastike me epityxia!"}

    except sqlite3.IntegrityError:
        # Edw pianoume to lathos tou "UNIQUE" pou legame pio prin!
        raise HTTPException(status_code=400, detail="Auto to timologio yparxei idi sto systima. Den epitrepetai diploxrewsi!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))