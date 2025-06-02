from flask import Flask, render_template, request, redirect, url_for
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

@app.route('/ajouter', methods=['GET', 'POST'])
def ajouter():
    if request.method == 'POST':
        date = request.form['date']
        produit = request.form['produit']
        quantite = int(request.form['quantite'])
        prix_unitaire = float(request.form['prix_unitaire'])
        client = request.form['client']
        
        conn = sqlite3.connect("db/ventes.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ventes (date, produit, quantite, prix_unitaire, client) VALUES (?, ?, ?, ?, ?)
        """, (date, produit, quantite, prix_unitaire, client)
        )
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
    
    return render_template('ajouter.html')

if __name__ == '__main__':
    app.run(debug=True)