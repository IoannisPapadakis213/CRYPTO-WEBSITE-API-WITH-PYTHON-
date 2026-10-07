import os
import sqlite3
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

app = FastAPI(title="ENTERSOFTONE B2B Integration API")

# Κλειδώνουμε τη διαδρομή της βάσης στον ίδιο φάκελο με το main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "erp_system.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
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

class InvoicePayload(BaseModel):
    document_number: str
    customer_name: str
    total_amount: float

# ---------------------------------------------------------
# ΠΟΡΤΑ 1: Δημιουργία Τιμολογίου (POST)
# ---------------------------------------------------------
@app.post("/api/invoices")
def create_invoice(invoice: InvoicePayload):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO commercial_documents 
            (document_number, customer_name, total_amount, document_type, status)
            VALUES (?, ?, ?, 'Invoice', 'Pending')
        ''', (invoice.document_number, invoice.customer_name, invoice.total_amount))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"To timologio {invoice.document_number} perastike me epityxia!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Auto to timologio yparxei idi sto systima. Den epitrepetai diploxrewsi!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# ΠΟΡΤΑ 2: Επιστροφή ΟΛΩΝ των Τιμολογίων σε JSON (GET)
# ---------------------------------------------------------
@app.get("/api/invoices")
def get_all_invoices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT document_number, customer_name, total_amount, document_type, status FROM commercial_documents")
    rows = cursor.fetchall()
    conn.close()
    
    invoices = []
    for r in rows:
        invoices.append({
            "document_number": r[0],
            "customer_name": r[1],
            "total_amount": r[2],
            "document_type": r[3],
            "status": r[4]
        })
    return {"invoices": invoices}

# ---------------------------------------------------------
# ΠΟΡΤΑ 3: Επιστροφή Ενός Τιμολογίου σε XML (GET)
# ---------------------------------------------------------
@app.get("/api/invoices/{doc_number}/xml")
def get_invoice_xml(doc_number: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT document_number, customer_name, total_amount FROM commercial_documents WHERE document_number = ?", (doc_number,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Το τιμολόγιο δεν βρέθηκε στη βάση δεδομένων.")

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice>
    <DocumentNumber>{row[0]}</DocumentNumber>
    <CustomerName>{row[1]}</CustomerName>
    <TotalAmount>{row[2]}</TotalAmount>
</Invoice>
"""
    return Response(content=xml_content, media_type="application/xml")