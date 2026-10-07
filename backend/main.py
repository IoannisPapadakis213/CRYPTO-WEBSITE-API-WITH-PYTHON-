import os
import sqlite3
import random
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

# Φορτώνουμε τις μεταβλητές από το .env αρχείο
load_dotenv()

app = FastAPI(title="ENTERSOFTONE B2B Integration Hub")

# Ενεργοποίηση CORS για επικοινωνία με το React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "erp_system.db")

# Ανάγνωση του Gemini API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY den vretheke sto .env!")

client = genai.Client(api_key=api_key)

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

# --- PYTHON FUNCTION GIA TO AI TOOL ---
def insert_invoice_to_db(document_number: str, customer_name: str, total_amount: float) -> str:
    """Prosthetei ena neo timologio stin SQL vasi tou ERP."""
    
    # Αν το AI δεν βρει ποσό και στείλει 0, εμείς δημιουργούμε ένα τυχαίο ποσό
    if total_amount <= 0:
        total_amount = round(random.uniform(50.0, 850.0), 2)
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO commercial_documents 
            (document_number, customer_name, total_amount, document_type, status)
            VALUES (?, ?, ?, 'Invoice', 'Pending')
        ''', (document_number, customer_name, float(total_amount)))
        conn.commit()
        conn.close()
        return f"To timologio {document_number} gia ton pelati {customer_name} me poso {total_amount} EUR kataxwristhke me epityxia stin SQL vasi."
    except sqlite3.IntegrityError:
        return f"Apotyxia: To timologio {document_number} yparxei idi stin SQL vasi (Duplicate Entry / Integrity Constraint)."
    except Exception as e:
        return f"Sfalma kata tin kataxwrisi: {str(e)}"

# --- PYDANTIC MODELS ---
class InvoicePayload(BaseModel):
    document_number: str
    customer_name: str
    total_amount: float

class ChatQuery(BaseModel):
    message: str

# --- API ENDPOINTS ---

@app.post("/api/invoices")
def create_invoice(invoice: InvoicePayload):
    res = insert_invoice_to_db(invoice.document_number, invoice.customer_name, invoice.total_amount)
    if "Apotyxia" in res:
        raise HTTPException(status_code=400, detail=res)
    return {"status": "success", "message": res}

@app.get("/api/invoices")
def get_all_invoices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT document_number, customer_name, total_amount, document_type, status FROM commercial_documents ORDER BY id DESC")
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

@app.get("/api/invoices/{doc_number}/xml")
def get_invoice_xml(doc_number: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT document_number, customer_name, total_amount FROM commercial_documents WHERE document_number = ?", (doc_number,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="To timologio den vretheke.")

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice>
    <DocumentNumber>{row[0]}</DocumentNumber>
    <CustomerName>{row[1]}</CustomerName>
    <TotalAmount>{row[2]}</TotalAmount>
    <Currency>EUR</Currency>
</Invoice>
"""
    return Response(content=xml_content, media_type="application/xml")

# --- AI COPILOT ENDPOINT ---

@app.post("/api/chat")
def chat_with_gemini(query: ChatQuery):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT document_number, customer_name, total_amount, status FROM commercial_documents")
        records = cursor.fetchall()
        conn.close()

        records_summary = "\n".join([f"- Doc: {r[0]}, Client: {r[1]}, Amount: {r[2]} EUR, Status: {r[3]}" for r in records])

        system_instruction = f"""
Eisai o official AI Integration Copilot gia to ERP B2B Hub tis ENTERSOFTONE.
Exeis amesi prosvasi stin SQL vasi kai mporeis na ekteleseis leitourgies mesw tool calling!

Kanonas Leitourgias:
1. An o xristis zhtisei na prostethei, na kataxwrithei h na dimiourgithei timologio, KALESE AMESWS ti synartisi `insert_invoice_to_db`.
2. An o xristis den dwsei poso ('total_amount'), perase tin timh 0.0 (h Python mas tha to frontisei).
3. An o xristis den dwsei 'document_number', ftiakse ena tyxaio san 'INV-XXX' opou XXX einai 3 grammata i arithmoi.
4. Apanta panta me epaggelmatiko, katharo yfos integration engineer sta Ellinika i ta Agglika analoga pws rwtise o xristis.

Trexonta dedomena sti vasi:
{records_summary if records_summary else "H vasi einai adeia ayth ti stigmi."}
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=query.message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[insert_invoice_to_db],
                temperature=0.2,
            )
        )

        final_reply = ""
        function_called = False

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_called = True
                    fn_name = part.function_call.name
                    fn_args = dict(part.function_call.args) if part.function_call.args else {}
                    
                    if fn_name == "insert_invoice_to_db":
                        if "document_number" not in fn_args or not fn_args["document_number"]:
                            fn_args["document_number"] = f"INV-{random.randint(200, 999)}"
                        if "total_amount" not in fn_args:
                            fn_args["total_amount"] = 0.0

                        tool_result = insert_invoice_to_db(**fn_args)
                        final_reply += f"{tool_result}\n"

        if function_called:
            final_reply += "\nΗ ενέργεια AI ολοκληρώθηκε επιτυχώς. Το UI θα ανανεωθεί."
        else:
            final_reply = response.text if response.text else "Μήπως μπορείτε να επαναλάβετε το αίτημα;"

        return {"reply": final_reply}
        
    except Exception as e:
        if "503" in str(e):
            raise HTTPException(status_code=503, detail="Το Gemini API έχει προσωρινά υψηλό φόρτο. Παρακαλώ προσπαθήστε ξανά σε λίγα δευτερόλεπτα.")
        raise HTTPException(status_code=500, detail=f"AI Agent Error: {str(e)}")