import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3
from datetime import datetime

app = FastAPI()

# --- CONFIGURACIÓN DE SEGURIDAD (CORS) ---
# Esto permite que tu frontend en React se comunique con este backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://uriroig-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELO DE DATOS ---
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    service: str
    message: str

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            service TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Iniciamos la base de datos al arrancar
init_db()

# --- RUTA PARA RECIBIR CONTACTOS ---
@app.post("/contact")
async def receive_contact(form: ContactForm):
    try:
        # 1. Guardar en SQLite (lo que ya tenías y funciona)
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO contacts (name, email, service, message, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (form.name, form.email, form.service, form.message, now))
        
        conn.commit()
        conn.close()

        # 2. ENVIAR A n8n (El cable nuevo)
        n8n_url = "https://n8n-production-4428.up.railway.app/webhook/contacto-web"
        payload = {
            "nombre": form.name,
            "email": form.email,
            "servicio": form.service,
            "mensaje": form.message,
            "fecha": now
        }
        
        # Intentamos enviar a n8n, pero si falla n8n que no se rompa la web
        try:
            requests.post(n8n_url, json=payload, timeout=5)
            print(f"✅ Lead enviado a n8n correctamente")
        except Exception as e_n8n:
            print(f"⚠️ Error enviando a n8n: {e_n8n}")

        print(f"✅ ¡Nuevo lead recibido de {form.name}!")
        return {"message": "Datos guardados y enviados", "status": "success"}

    except Exception as e:
        print(f"❌ Error al guardar: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/")
def read_root():
    return {"status": "Backend de Uri Roig funcionando 🚀"}
