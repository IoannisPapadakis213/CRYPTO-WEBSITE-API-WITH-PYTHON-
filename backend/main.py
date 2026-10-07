import os
from fastapi import FastAPI, HTTPException
import requests
import pandas as pd
import json

app = FastAPI(title="Crypto Integration Hub API - My Original Code")

URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
API_KEY = '0ad53085-1cb2-4eb8-ad9e-3ffbd7e56509'
CSV_FILE = 'API.csv' # Το αρχείο που θα αποθηκεύονται τα δεδομένα σου

# ---------------------------------------------------------
# Η ΔΙΚΗ ΣΟΥ ΣΥΝΑΡΤΗΣΗ: Τραβάει δεδομένα και τα σώζει στο CSV
# ---------------------------------------------------------
def api_runner():
    parameters = {
      'start':'1',
      'limit':'15',
      'convert':'USD'
    }
    headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': API_KEY,
    }

    try:
        response = requests.get(URL, params=parameters, headers=headers)
        response.raise_for_status()
        data = json.loads(response.text)
        
        # Ο δικός σου κώδικας pandas ακριβώς όπως τον έγραψες
        df = pd.json_normalize(data['data'])
        df['timestamp'] = pd.to_datetime('now')
        
        # Ελέγχουμε αν υπάρχει το αρχείο για να κάνουμε append ή δημιουργία
        if not os.path.isfile(CSV_FILE):
            df.to_csv(CSV_FILE, header=True, index=False)
        else:
            df.to_csv(CSV_FILE, mode='a', header=False, index=False)
            
        return {"status": "success", "message": "Τα δεδομένα αποθηκεύτηκαν στο API.csv επιτυχώς!"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# ΠΟΡΤΑ 1: Εκτελεί τον κώδικά σου χειροκίνητα
# ---------------------------------------------------------
@app.get("/api/run-script")
def run_my_script():
    # Όταν μπαίνεις σε αυτό το link, τρέχει η συνάρτησή σου api_runner()
    result = api_runner()
    return result

# ---------------------------------------------------------
# ΠΟΡΤΑ 2: Η Ανάλυση Trends (Από τον δικό σου κώδικα)
# ---------------------------------------------------------
@app.get("/api/trends")
def get_crypto_trends():
    # Ελέγχουμε αν έχεις τρέξει το script έστω μια φορά για να υπάρχει το CSV
    if not os.path.isfile(CSV_FILE):
        raise HTTPException(status_code=404, detail="Το αρχείο API.csv δεν υπάρχει. Τρέξε πρώτα το /api/run-script")
        
    # Διαβάζουμε το αρχείο όπως έκανες στο Jupyter
    df = pd.read_csv(CSV_FILE)
    
    # Η δικιά σου λογική ομαδοποίησης (groupby)
    # Βρίσκουμε τον μέσο όρο (mean) των αλλαγών για κάθε νόμισμα
    df_trends = df.groupby('name', sort=False)[['quote.USD.percent_change_1h',
                                                'quote.USD.percent_change_24h',
                                                'quote.USD.percent_change_7d']].mean()
    
    # Επιστρέφουμε τα αποτελέσματα της ανάλυσής σου σε μορφή JSON
    # Το .to_dict() μετατρέπει το DataFrame σε μορφή που καταλαβαίνει το API
    return df_trends.to_dict(orient="index")