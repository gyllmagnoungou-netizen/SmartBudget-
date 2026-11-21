from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_mem_123456")

os.makedirs("database", exist_ok=True)

def init_db():
    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS depenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT NOT NULL,
            date_depense TEXT NOT NULL,
            utilisateur_id INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revenus(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            montant REAL NOT NULL,
            date_revenu TEXT NOT NULL,
            utilisateur_id INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objectifs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            montant_cible REAL NOT NULL,
            utilisateur_id INTEGER NOT NULL,
            atteint INTEGER DEFAULT 0
        )
    """)
    # Pour les anciennes bases sans la colonne atteint
    try:
        cursor.execute("ALTER TABLE objectifs ADD COLUMN atteint INTEGER DEFAULT 0")
    except:
        pass

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def accueil():
    if "user_id" in session:
        return redirect("/dashboard")
    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM depenses")
    depenses = cursor.fetchall()
    cursor.execute("SELECT * FROM revenus")
    revenus = cursor.fetchall()
    cursor.execute("SELECT SUM(montant) FROM depenses")
    r = cursor.fetchone()
    total_depenses = r[0] if r and r[0] is not None else 0
    cursor.execute("SELECT SUM(montant) FROM revenus")
    r = cursor.fetchone()
    total_revenus = r[0] if r and r[0] is not None else 0
    solde = total_revenus - total_depenses
    conn.close()
    return render_template("index.html", depenses=depenses, revenus=revenus,
        total_depenses=total_depenses, total_revenus=total_revenus,
        solde=solde, graphique_depenses=total_depenses, graphique_revenus=total_revenus)

@app.route("/ajouter", methods=["GET", "POST"])
def ajouter_depense():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        description = request.form["description"]
        montant = request.form["montant"]
        categorie = request.form["categorie"]
        date_depense = request.form["date_depense"]
        utilisateur_id = session["user_id"]
        conn = sqlite3.connect("database/budget.db")
        cursor = conn.cursor()
        cursor.execute("""
           INSERT INTO depenses (description, montant, categorie, date_depense, utilisateur_id)
           VALUES (?, ?, ?, ?, ?)
        """, (description, montant, categorie, date_depense, utilisateur_id))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return render_template("ajout_depense.html")

@app.route("/ajouter_revenu", methods=["GET", "POST"])
def ajouter_revenu():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        source = request.form["source"]
        montant = request.form["montant"]
        date_revenu = request.form["date_revenu"]
        utilisateur_id = session["user_id"]
        conn = sqlite3.connect("database/budget.db")
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO revenus (source, montant, date_revenu, utilisateur_id)
                VALUES (?, ?, ?, ?)
            """, (source, montant, date_revenu, utilisateur_id))
            conn.commit()
        except Exception as e:
            print("ERREUR :", e)
        finally:
            conn.close()
        return redirect("/dashboard")
    return render_template("ajout_revenu.html")

@app.route("/supprimer_depense/<int:id>")
def supprimer_depense(id):
    if "user_id" not in session:
        return redirect("/login")
    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM depenses WHERE id=? AND utilisateur_id=?", (id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/reinitialiser")
def reinitialiser():
    if "user_id" not in session:
        return redirect("/login")
    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM depenses WHERE utilisateur_id=?", (session["user_id"],))
    cursor.execute("DELETE FROM revenus WHERE utilisateur_id=?", (session["user_id"],))
    cursor.execute("DELETE FROM objectifs WHERE utilisateur_id=?", (session["user_id"],))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nom = request.form["nom"]
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]
        conn = sqlite3.connect("database/budget.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateurs WHERE email=?", (email,))
        utilisateur = cursor.fetchone()
        if utilisateur:
            conn.close()
            return "Cet email existe déjà."
        mot_de_passe_hash = generate_password_hash(mot_de_passe)
        cursor.execute("INSERT INTO utilisateurs (nom,email,mot_de_passe) VALUES (?,?,?)", (nom, email, mot_de_passe_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        session["user_id"] = user_id
        session["user_nom"] = nom
        return redirect("/dashboard")
    return render_template("auth/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        mot_de_passe = request.form["mot_de_passe"]
        conn = sqlite3.connect("database/budget.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateurs WHERE email=?", (email,))
        utilisateur = cursor.fetchone()
        conn.close()
        if utilisateur and check_password_hash(utilisateur[3], mot_de_passe):
            session["user_id"] = utilisateur[0]
            session["user_nom"] = utilisateur[1]
            return redirect("/dashboard")
        return "Email ou mot de passe incorrect"
    return render_template("auth/login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM depenses WHERE utilisateur_id=? ORDER BY id DESC", (session["user_id"],))
    depenses = cursor.fetchall()

    cursor.execute("SELECT SUM(montant) FROM depenses WHERE utilisateur_id=?", (session["user_id"],))
    r = cursor.fetchone()
    total_depenses = r[0] if r and r[0] is not None else 0

    cursor.execute("SELECT categorie, SUM(montant) FROM depenses WHERE utilisateur_id=? GROUP BY categorie", (session["user_id"],))
    categories = cursor.fetchall()
    categorie_dominante = ""
    if categories:
        categorie_dominante = max(categories, key=lambda x: x[1])[0]

    cursor.execute("SELECT * FROM revenus WHERE utilisateur_id=? ORDER BY id DESC", (session["user_id"],))
    revenus = cursor.fetchall()

    cursor.execute("SELECT SUM(montant) FROM revenus WHERE utilisateur_id=?", (session["user_id"],))
    r = cursor.fetchone()
    total_revenus = r[0] if r and r[0] is not None else 0

    solde = total_revenus - total_depenses

    taux_epargne = 0
    if total_revenus > 0:
        taux_epargne = round((solde / total_revenus) * 100, 1)

    score = 0
    if total_revenus > 0:
        taux_depenses = (total_depenses / total_revenus) * 100
        if taux_depenses > 100:
            score = 20
        elif taux_depenses > 80:
            score = 50
        elif taux_depenses > 60:
            score = 75
        else:
            score = 95

    conseil = ""
    if total_revenus == 0:
        conseil = "Bienvenu sur SmartBudget. Commencez par ajouter vos premieres opérations."
    elif solde < 0:
        conseil = f"⚠ Attention ! Vous dépensez plus que vos revenus. Votre solde est négatif de {abs(solde)} FCFA. Réduisez vos dépenses immédiatement."
    elif taux_epargne < 10:
        conseil = f"Votre taux d'épargne est seulement de {taux_epargne}%. Essayez de réduire certaines dépenses."
    elif taux_epargne < 20:
        conseil = f"Votre taux d'épargne est de {taux_epargne}%. Situation correcte mais améliorable."
    else:
        conseil = f"Excellent ! Votre taux d'épargne est de {taux_epargne}%. Continuez comme ça."

    if categorie_dominante:
        conseil += f"\n\nVotre principal poste de depense est : {categorie_dominante}. Analysez cette catégorie pour trouver de nouvelles économies."

    # ===== CORRIGÉ : OBJECTIF - PLUS DE VALEURS PAR DÉFAUT 1 =====
    objectif_id = None
    objectif_atteint = 0
    titre_objectif = None
    montant_cible = 0
    progression = 0
    mois_objectif = 0

    cursor.execute("SELECT id, titre, montant_cible, atteint FROM objectifs WHERE utilisateur_id=? LIMIT 1", (session["user_id"],))
    objectif = cursor.fetchone()

    if objectif:
        objectif_id = objectif[0]
        titre_objectif = objectif[1]
        montant_cible = objectif[2]
        objectif_atteint = objectif[3]

        if montant_cible and montant_cible > 0:
            progression = min(round((solde / montant_cible) * 100), 100)
            if solde > 0:
                mois_objectif = round(montant_cible / solde)

    conn.close()
    return render_template("dashboard.html",
        nom=session["user_nom"], depenses=depenses, revenus=revenus,
        total_depenses=total_depenses, total_revenus=total_revenus,
        solde=solde, categories=categories, categorie_dominante=categorie_dominante,
        conseil=conseil, score=score, taux_epargne=taux_epargne,
        titre_objectif=titre_objectif, montant_cible=montant_cible,
        progression=progression, mois_objectif=mois_objectif, objectif_id=objectif_id, objectif_atteint=objectif_atteint)

@app.route("/objectif", methods=["GET", "POST"])
def objectif():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        titre = request.form["titre"]
        montant_cible = request.form["montant_cible"]
        conn = sqlite3.connect("database/budget.db")
        cursor = conn.cursor()
        # On supprime l'ancien objectif s'il existe, pour n'en avoir qu'un seul
        cursor.execute("DELETE FROM objectifs WHERE utilisateur_id=?", (session["user_id"],))
        cursor.execute("INSERT INTO objectifs (titre, montant_cible, utilisateur_id, atteint) VALUES (?,?,?,0)", (titre, montant_cible, session["user_id"]))
        conn.commit()
        conn.close()
        return redirect("/dashboard")
    return render_template("objectif.html")

@app.route("/objectif_atteint/<int:id>")
def objectif_atteint(id):
    if "user_id" not in session:
        return redirect("/login")
    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()
    # On vérifie que l'objectif appartient bien à l'utilisateur
    cursor.execute("SELECT * FROM objectifs WHERE id=? AND utilisateur_id=?", (id, session["user_id"]))
    obj = cursor.fetchone()
    if obj:
        # On le marque comme atteint puis on le supprime pour RÉINITIALISER
        cursor.execute("UPDATE objectifs SET atteint=1 WHERE id=?", (id,))
        conn.commit()
        cursor.execute("DELETE FROM objectifs WHERE id=? AND utilisateur_id=?", (id, session["user_id"]))
        conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/test_db")
def test_db():
    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(objectifs)")
    colonnes = cursor.fetchall()
    conn.close()
    return str(colonnes)

@app.route("/supprimer_compte", methods=["GET", "POST"])
def supprimer_compte():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        mot_de_passe = request.form.get("mot_de_passe")
        conn = sqlite3.connect("database/budget.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateurs WHERE id=?", (session["user_id"],))
        utilisateur = cursor.fetchone()
        if utilisateur and check_password_hash(utilisateur[3], mot_de_passe):
            uid = session["user_id"]
            cursor.execute("DELETE FROM depenses WHERE utilisateur_id=?", (uid,))
            cursor.execute("DELETE FROM revenus WHERE utilisateur_id=?", (uid,))
            cursor.execute("DELETE FROM objectifs WHERE utilisateur_id=?", (uid,))
            cursor.execute("DELETE FROM utilisateurs WHERE id=?", (uid,))
            conn.commit()
            conn.close()
            session.clear()
            return redirect("/login")
        conn.close()
        return render_template("supprimer_compte.html", error="Mot de passe incorrect")
    return render_template("supprimer_compte.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))