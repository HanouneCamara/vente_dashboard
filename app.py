from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

# Récupérer les ventes
def get_all_ventes():
    conn = sqlite3.connect("db/ventes.db")
    conn.row_factory = sqlite3.Row #Accéder aux colonnes
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ventes")
    ventes = cursor.fetchall()
    conn.close()
    return ventes

@app.route('/')
def index():
    ventes = get_all_ventes()
    return render_template('index.html', ventes=ventes)

if __name__ == '__main__':
    app.run(debug=True)