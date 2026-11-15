from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# Création du dossier database
os.makedirs("database", exist_ok=True)


# Initialisation de la base
def init_db():

    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()

    # Table dépenses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS depenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT NOT NULL,
            date_depense TEXT NOT NULL
        )
    """)

    # Table revenus
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revenus(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            montant REAL NOT NULL,
            date_revenu TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# Page d'accueil
@app.route("/")
def accueil():

    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()

    # Liste des dépenses
    cursor.execute("SELECT * FROM depenses")
    depenses = cursor.fetchall()

    # Liste des revenus
    cursor.execute("SELECT * FROM revenus")
    revenus = cursor.fetchall()

    # Total des dépenses
    cursor.execute("SELECT SUM(montant) FROM depenses")
    total_depenses = cursor.fetchone()[0]

    if total_depenses is None:
        total_depenses = 0

    # Total des revenus
    cursor.execute("SELECT SUM(montant) FROM revenus")
    total_revenus = cursor.fetchone()[0]

    if total_revenus is None:
        total_revenus = 0

    # Calcul du solde
    solde = total_revenus - total_depenses

    conn.close()

    return render_template(
        "index.html",
        depenses=depenses,
        revenus=revenus,
        total_depenses=total_depenses,
        total_revenus=total_revenus,
        solde=solde,
        graphique_depenses=total_depenses,
        graphique_revenus=total_revenus,
    )


# Ajouter une dépense
@app.route("/ajouter", methods=["GET", "POST"])
def ajouter_depense():

    if request.method == "POST":

        description = request.form["description"]
        montant = request.form["montant"]
        categorie = request.form["categorie"]
        date_depense = request.form["date_depense"]

        conn = sqlite3.connect("database/budget.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO depenses
            (description, montant, categorie, date_depense)
            VALUES (?, ?, ?, ?)
        """, (
            description,
            montant,
            categorie,
            date_depense
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("ajout_depense.html")


# Ajouter un revenu
@app.route("/ajouter_revenu", methods=["GET", "POST"])
def ajouter_revenu():

    if request.method == "POST":

        source = request.form["source"]
        montant = request.form["montant"]
        date_revenu = request.form["date_revenu"]

        conn = sqlite3.connect("database/budget.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO revenus
            (source, montant, date_revenu)
            VALUES (?, ?, ?)
        """, (
            source,
            montant,
            date_revenu
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("ajout_revenu.html")

@app.route("/supprimer_depense/<int:id>")
def supprimer_depense(id):

    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM depenses WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")
@app.route("/reinitialiser")
def reinitialiser():

    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM depenses")
    cursor.execute("DELETE FROM revenus")

    conn.commit()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )