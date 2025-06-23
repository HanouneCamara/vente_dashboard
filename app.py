from flask import Flask, render_template, request, redirect, url_for, make_response, send_file
import sqlite3
from xhtml2pdf import pisa
from io import BytesIO
import openpyxl
from datetime import datetime


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

def get_stats(mois=None, annee=None):
    conn = sqlite3.connect("db/ventes.db")
    cursor = conn.cursor()

    # Préparer les filtres SQL
    condition = ""
    params = []

    if mois and annee:
        condition = "WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params = [f"{mois:02d}", str(annee)]

    # Total des ventes (
    cursor.execute(f"SELECT SUM(quantite * prix_unitaire) FROM ventes {condition}", params)
    total_ventes = cursor.fetchone()[0] or 0

    # Total des quantités
    cursor.execute(f"SELECT SUM(quantite) FROM ventes {condition}", params)
    total_quantite = cursor.fetchone()[0] or 0

    # Meilleur client
    cursor.execute(f"""
        SELECT client, COUNT(*) as ventes
        FROM ventes
        {condition}
        GROUP BY client
        ORDER BY ventes DESC LIMIT 1
    """, params)
    best_client = cursor.fetchone()
    client_nom = best_client[0] if best_client else "Aucun"
    client_ventes = best_client[1] if best_client else 0

    # Produit le plus vendu
    cursor.execute(f"""
        SELECT produit, SUM(quantite) as total
        FROM ventes
        {condition}
        GROUP BY produit
        ORDER BY total DESC LIMIT 1 
    """, params)
    best_produit = cursor.fetchone()
    produit_nom = best_produit[0] if best_produit else "Aucun"
    produit_total = best_produit[1] if best_produit else 0

    conn.close()
    return {
        "total_ventes": total_ventes,
        "total_quantite": total_quantite,
        "client_nom": client_nom,
        "client_ventes": client_ventes,
        "produit_nom": produit_nom,
        "produit_total": produit_total
    }

@app.route('/dashboard')
def dashboard():
    # Récupération des filtres depuis l'URL
    mois = request.args.get('mois', type=int)
    annee = request.args.get('annee', type=int)

    # Connexion à la base
    conn = sqlite3.connect("db/ventes.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Conditions SQL selon les filtres
    condition = ""
    params = []

    if mois and annee:
        condition = "WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?"
        params = [f"{mois:02d}", str(annee)]

    # Récupération des ventes filtrées
    cursor.execute(f"SELECT * FROM ventes {condition}", params)
    ventes = cursor.fetchall()
    conn.close()

    # Données pour l’histogramme par produit
    produit_totaux = {}
    for vente in ventes:
        produit = vente["produit"]
        produit_totaux[produit] = produit_totaux.get(produit, 0) + vente["quantite"]
    labels_produits = list(produit_totaux.keys())
    quantites_produits = list(produit_totaux.values())

    # Données pour le camembert par client
    client_totaux = {}
    for vente in ventes:
        client = vente["client"]
        client_totaux[client] = client_totaux.get(client, 0) + vente["quantite"]
    labels_clients = list(client_totaux.keys())
    quantites_clients = list(client_totaux.values())

    # Évolution des ventes par mois 
    toutes_ventes = get_all_ventes()
    ventes_par_mois = {}
    for vente in toutes_ventes:
        date_obj = datetime.strptime(vente['date'], '%Y-%m-%d')
        mois_annee = date_obj.strftime('%Y-%m')
        ventes_par_mois[mois_annee] = ventes_par_mois.get(mois_annee, 0) + vente['quantite']
    labels_mois = sorted(ventes_par_mois.keys())
    quantites_mois = [ventes_par_mois[m] for m in labels_mois]

    # Statistiques générales
    stats = get_stats(mois, annee)

    return render_template(
        'dashboard.html',
        labels=labels_produits,
        quantites=quantites_produits,
        labels_clients=labels_clients,
        quantites_clients=quantites_clients,
        labels_mois=labels_mois,
        quantites_mois=quantites_mois,
        stats=stats,
        mois_selected=mois,
        annee_selected=annee
    )
        
if __name__ == '__main__':
    app.run(debug=True)