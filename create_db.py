import sqlite3
import os

# Vérifier si le dossier "db" existe
if not os.path.exists("db"):
    os.makedirs("db")
    
# Connexion à la bdd
conn = sqlite3.connect("db/ventes.db")
cursor = conn.cursor()

# Création de la table ventes
cursor.execute("""
CREATE TABLE IF NOT EXISTS ventes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    produit TEXT,
    quantite INTEGER,
    prix_unitaire REAL,
    client TEXT
)   
""")
conn.commit()
conn.close()

print("Base de données creer")