from flask import Flask, render_template, request, redirect, url_for, make_response, send_file
import sqlite3
from xhtml2pdf import pisa
from io import BytesIO
import openpyxl

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

# Fonction qui calcule les totaux
def get_totaux():
    conn = sqlite3.connect("db/ventes.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(quantite * prix_unitaire) FROM ventes")
    total_ventes = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(quantite) FROM ventes")
    total_quantite = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return total_ventes, total_quantite

@app.route('/')
def index():
    ventes = get_all_ventes()
    total_ventes, total_quantite = get_totaux()
    return render_template('index.html', ventes=ventes, total_ventes=total_ventes, total_quantite=total_quantite)

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

@app.route('/supprimer/<int:id>', methods=['GET', 'POST'])
def supprimer(id):
    conn = sqlite3.connect("db/ventes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ventes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier(id):
    conn = sqlite3.connect("db/ventes.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if request.method == 'POST':
        date = request.form['date']
        produit = request.form['produit']
        quantite = int(request.form['quantite'])
        prix_unitaire = float(request.form['prix_unitaire'])
        client = request.form['client']
        
        cursor.execute("""
            UPDATE ventes
            SET date = ?, produit = ?, quantite = ?, prix_unitaire = ?, client = ?
            WHERE id = ?
        """,(date, produit, quantite, prix_unitaire, client, id)
        )
        
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    cursor.execute("SELECT * FROM ventes WHERE id = ?", (id,))
    vente = cursor.fetchone()
    conn.close()
    return render_template('modifier.html', vente=vente)

@app.route('/reports/pdf')
def generer_pdf():
    ventes = get_all_ventes()
    rendered = render_template("rapport_pdf.html", ventes=ventes)
    
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(rendered, dest=pdf)
    
    if not pisa_status.err:
        pdf.seek(0)
        return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name='rapport_ventes.pdf')
    return "Erreur lors de la génération du PDF"

@app.route('/reports/excel')
def generer_excel():
    ventes = get_all_ventes()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ventes"

    # Entête
    ws.append(["ID", "Date", "Produit", "Quantité", "Prix Unitaire", "Client"])

    # Données
    for v in ventes:
        ws.append([v["id"], v["date"], v["produit"], v["quantite"], v["prix_unitaire"], v["client"]])

    # Sauvegarde en mémoire
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='rapport_ventes.xlsx')

@app.route('/dashboard')
def dashboard():
    ventes = get_all_ventes()
    
    # Les données pour les graphique
    labels_produits = []
    quantites_produits = []
    
    for vente in ventes:
        labels_produits.append(vente['produit'])
        quantites_produits.append(vente['quantite'])
         
    # total quantité par client
    client_totaux = {}
    for vente in ventes:
        client = vente['client']
        quantite = vente['quantite']
        if client in client_totaux:
            client_totaux[client] += quantite
        else:
            client_totaux[client] = quantite
    
    labels_clients = list(client_totaux.keys())
    quantites_clients = list(client_totaux.values())
    
    return render_template('dashboard.html', labels=labels_produits, quantites=quantites_produits, labels_clients=labels_clients, quantites_clients=quantites_clients)

        
if __name__ == '__main__':
    app.run(debug=True)