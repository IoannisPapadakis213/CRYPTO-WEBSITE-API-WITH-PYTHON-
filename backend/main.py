# Φέρνουμε τα "τουβλάκια" για να χτίσουμε το API (τον σερβιτόρο)
from fastapi import FastAPI, HTTPException

# Φέρνουμε το εργαλείο που μιλάει με το CoinMarketCap
import requests 

# Δημιουργούμε τον σερβιτόρο μας και του δίνουμε το όνομα "app"
app = FastAPI(title="Crypto Integration Hub API")

# Βάζουμε τα στοιχεία σου για το CoinMarketCap
URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
API_KEY = '0ad53085-1cb2-4eb8-ad9e-3ffbd7e56509'

# ---------------------------------------------------------
# ΠΟΡΤΑ 1: Η Αρχική Σελίδα (Το καλωσόρισμα)
# ---------------------------------------------------------
@app.get("/")
def read_root():
    # Όποιος μπαίνει εδώ, βλέπει απλά ένα μήνυμα καλωσορίσματος
    return {"message": "Καλώς ήρθες στο API μας!"}

# ---------------------------------------------------------
# ΠΟΡΤΑ 2: Εδώ παίρνουμε τα δεδομένα των κρυπτονομισμάτων
# ---------------------------------------------------------
@app.get("/api/crypto")
def get_crypto_data():
    # Αυτοί είναι οι κανόνες (παράμετροι) που ζητάει το CoinMarketCap
    parameters = {
      'start': '1',
      'limit': '15',
      'convert': 'USD'
    }
    
    # Εδώ βάζουμε το "πάσο" μας (το API KEY) για να μας αφήσουν να μπούμε
    headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': API_KEY,
    }

    try:
        # Ο σερβιτόρος μας πάει στο CoinMarketCap και ζητάει τα δεδομένα
        response = requests.get(URL, params=parameters, headers=headers)
        
        # Αν όλα πάνε καλά, ανοίγουμε το πακέτο (JSON) και το διαβάζουμε
        data = response.json()
        
        # Το δίνουμε πίσω σε όποιον το ζήτησε
        return {"status": "success", "data": data['data']}
        
    except Exception as e:
        # Αν κάτι πάει στραβά (π.χ. κοπεί το ίντερνετ), βγάζουμε ένα μήνυμα λάθους
        raise HTTPException(status_code=500, detail=f"Κάτι πήγε στραβά: {str(e)}")