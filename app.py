from flask import Flask, jsonify, request, render_template, abort
from dataclasses import dataclass
from typing import List
import threading

app = Flask(__name__)
lock = threading.Lock()

# ---------- Domain classes ----------
@dataclass
class Serbatoio:
    capacita: float
    livello: float

    def percentuale(self):
        if self.capacita == 0:
            return 0.0
        return (self.livello / self.capacita) * 100

@dataclass
class Distributore:
    id: int
    nome: str
    provincia: str
    indirizzo: str
    lat: float
    lon: float
    serbatoio_benzina: Serbatoio
    serbatoio_diesel: Serbatoio
    prezzo_benzina: float
    prezzo_diesel: float

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "provincia": self.provincia,
            "indirizzo": self.indirizzo,
            "lat": self.lat,
            "lon": self.lon,
            "livello_benzina": self.serbatoio_benzina.livello,
            "capacita_benzina": self.serbatoio_benzina.capacita,
            "percent_benzina": self.serbatoio_benzina.percentuale(),
            "livello_diesel": self.serbatoio_diesel.livello,
            "capacita_diesel": self.serbatoio_diesel.capacita,
            "percent_diesel": self.serbatoio_diesel.percentuale(),
            "prezzo_benzina": self.prezzo_benzina,
            "prezzo_diesel": self.prezzo_diesel
        }

# ---------- Sample data ----------
_distributori: List[Distributore] = [
    Distributore(
        id=1,
        nome="IPERSTAR Ovest",
        provincia="MI",
        indirizzo="Via Roma 10, Milano",
        lat=45.4642,
        lon=9.1900,
        serbatoio_benzina=Serbatoio(10000, 7000),
        serbatoio_diesel=Serbatoio(12000, 9000),
        prezzo_benzina=1.90,
        prezzo_diesel=1.80
    ),
    Distributore(
        id=2,
        nome="IPERSTAR Sud",
        provincia="MI",
        indirizzo="Piazza Duomo 1, Milano",
        lat=45.4643,
        lon=9.1910,
        serbatoio_benzina=Serbatoio(8000, 2000),
        serbatoio_diesel=Serbatoio(10000, 4000),
        prezzo_benzina=1.92,
        prezzo_diesel=1.82
    ),
    Distributore(
        id=3,
        nome="IPERSTAR Nord",
        provincia="TO",
        indirizzo="Corso Francia 2, Torino",
        lat=45.0703,
        lon=7.6869,
        serbatoio_benzina=Serbatoio(9000, 9000),
        serbatoio_diesel=Serbatoio(11000, 5000),
        prezzo_benzina=1.95,
        prezzo_diesel=1.85
    ),
]

# ---------- Utility ----------
def find_by_id(did: int):
    for d in _distributori:
        if d.id == did:
            return d
    return None

# ---------- Routes ----------
@app.route('/')
def homepage():
    return render_template("index.html")

@app.route('/api/distributori', methods=['GET'])
def api_elenco_distributori():
    with lock:
        ordinati = sorted(_distributori, key=lambda x: x.id)
        return jsonify([d.to_dict() for d in ordinati])

@app.route('/api/distributori/provincia/<string:provincia>/livelli', methods=['GET'])
def api_livelli_provincia(provincia):
    with lock:
        selezionati = [d.to_dict() for d in _distributori if d.provincia.lower() == provincia.lower()]
        return jsonify(selezionati)

@app.route('/api/distributori/<int:did>/livelli', methods=['GET'])
def api_livelli_distributore(did):
    with lock:
        d = find_by_id(did)
        if not d:
            abort(404, "Distributore non trovato")
        return jsonify(d.to_dict())

@app.route('/api/distributori/map', methods=['GET'])
def api_mappa():
    with lock:
        return jsonify([{
            "id": d.id,
            "nome": d.nome,
            "provincia": d.provincia,
            "lat": d.lat,
            "lon": d.lon,
            "prezzo_benzina": d.prezzo_benzina,
            "prezzo_diesel": d.prezzo_diesel,
            "livello_benzina": d.serbatoio_benzina.livello,
            "livello_diesel": d.serbatoio_diesel.livello
        } for d in _distributori])

@app.route('/api/distributori/provincia/<string:provincia>/prezzi', methods=['PUT'])
def api_cambia_prezzi_provincia(provincia):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Richiesta JSON mancante"}), 400

    aggiornati = []
    with lock:
        for d in _distributori:
            if d.provincia.lower() == provincia.lower():
                if 'benzina' in data:
                    d.prezzo_benzina = float(data['benzina'])
                if 'diesel' in data:
                    d.prezzo_diesel = float(data['diesel'])
                aggiornati.append(d.id)
    return jsonify({"aggiornati": aggiornati})

# ---------- Production server ----------
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)