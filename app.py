import time
import os
import qrcode
import io
import base64
from flask import Flask, render_template, request
from geopy.distance import geodesic
from dotenv import load_dotenv 
load_dotenv()

app = Flask(__name__)

# --- CONFIGURACIÓN DESDE .ENV ---
# Si no existen en el .env, usa valores por defecto
LAT = float(os.getenv('LAT_INSTITUCION', -34.6037))
LON = float(os.getenv('LON_INSTITUCION', -58.3816))
PUNTO_CONTROL = (LAT, LON)
RANGO_METROS = 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validar')
def validar():
    try:
        lat_user = request.args.get('lat')
        lon_user = request.args.get('lon')
        token_cliente = request.args.get('t')

        if not lat_user or not lon_user or not token_cliente:
             return render_template('validar.html', 
                                   error="Faltan datos de ubicación o token.", 
                                   tipo="danger"), 400

        # VALIDACIÓN DE TIEMPO
        token_actual = int(time.time() / 60)
        if abs(token_actual - int(token_cliente)) > 2:
            return render_template('validar.html', 
                                   error="QR Expirado. Escanea el código nuevo.", 
                                   tipo="warning"), 403

        # VALIDACIÓN DE DISTANCIA
        distancia = geodesic(PUNTO_CONTROL, (float(lat_user), float(lon_user))).meters
        
        if distancia <= RANGO_METROS:
            return render_template('validar.html', 
                                   exito=True, 
                                   distancia=round(distancia, 2))
        else:
            return render_template('validar.html', 
                                   error="Fuera de rango.", 
                                   distancia=round(distancia, 2), 
                                   tipo="danger"), 403

    except Exception as e:
        return render_template('validar.html', error=str(e), tipo="danger"), 400

@app.route('/institucion')
def pantalla_qr():
    url_base = request.host_url.rstrip('/')
    timestamp = int(time.time() / 60)
    # Importante: el QR debe apuntar a la URL donde el usuario valida su posición
    url_dinamica = f"{url_base}/validar?t={timestamp}"
    
    img = qrcode.make(url_dinamica)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('institucion.html', qr_code=qr_b64)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)