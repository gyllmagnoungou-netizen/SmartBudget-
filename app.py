from flask import Flask, render_template, request, redirect
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

app = Flask(__name__)
app.secret_key = "smartbudget_v2_secret"

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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utilisateurs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        mot_de_passe TEXT NOT NULL
        )
    """) 

    try:

       cursor.execute("""
        ALTER TABLE depenses
        ADD COLUMN utilisateur_id INTEGER
        """)

    except:
        pass 
  
    try:

       cursor.execute("""
        ALTER TABLE revenus 
        ADD COLUMN utilisateur_id INTEGER
        """)
    except:
       pass  


    conn.commit()
    conn.close()


init_db()


# Page d'accueil
@app.route("/")
def accueil():

    if "user_id" in session:
        return redirect("/dashboard")

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
        print("USER CONNECTE :", session["user_id"])

        cursor.execute("""
           INSERT INTO depenses
          ( description, montant,  categorie, date_depense,utilisateur_id)
          VALUES (?, ?, ?, ?, ?)
        """, (
            description,
            montant,
            categorie,
           date_depense,
           utilisateur_id,
            ))     
    

        conn.commit()
        conn.close()
        return redirect("/dashboard")
                

    return render_template("ajout_depense.html")



# Ajouter un revenu

@app.route("/ajouter_revenu", methods=["GET", "POST"])
def ajouter_revenu():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        print("FORMULAIRE RECU")
        print(request.form)

        source = request.form["source"]
        montant = request.form["montant"]
        date_revenu = request.form["date_revenu"]

        utilisateur_id = session["user_id"]

        print("USER =", utilisateur_id)

        conn = sqlite3.connect("database/budget.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO revenus
                (
                    source,
                    montant,
                    date_revenu,
                    utilisateur_id
                )
                VALUES (?, ?, ?, ?)
            """, (
                source,
                montant,
                date_revenu,
                utilisateur_id
            ))

            conn.commit()

            print("REVENU AJOUTE")

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

    cursor.execute(
    """
    DELETE FROM depenses
    WHERE id=? AND utilisateur_id=?
    """,
    (
        id,
        session["user_id"]
    )
)
    

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/reinitialiser")
def reinitialiser():
    if "user_id" not in session:
        return redirect("/login")
    
    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM depenses
        WHERE utilisateur_id=?
        """,
        (session["user_id"],)
    )
    cursor.execute(
        """
        DELETE FROM revenus
        WHERE utilisateur_id=?
        """,
        (session["user_id"],)
    )

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

        cursor.execute(
            "SELECT * FROM utilisateurs WHERE email=?",
            (email,)
        )

        utilisateur = cursor.fetchone()

        if utilisateur:
            conn.close()
            return "Cet email existe déjà."

        mot_de_passe_hash = generate_password_hash(
            mot_de_passe
        )

        cursor.execute("""
            INSERT INTO utilisateurs
            (nom,email,mot_de_passe)
            VALUES (?,?,?)
        """,
        (
            nom,
            email,
            mot_de_passe_hash
        ))

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

        cursor.execute(
            "SELECT * FROM utilisateurs WHERE email=?",
            (email,)
        )

        utilisateur = cursor.fetchone()

        conn.close()

        if utilisateur and check_password_hash(
            utilisateur[3],
            mot_de_passe
        ):

            session["user_id"] = utilisateur[0]
            session["user_nom"] = utilisateur[1]

            return redirect("/dashboard")

        return "Email ou mot de passe incorrect"

    return render_template("auth/login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")
    print("Utlilisateur connecté :", session["user_id"]) 

    conn = sqlite3.connect("database/budget.db")
    cursor = conn.cursor()

    cursor.execute(
    """
    SELECT * FROM depenses
    WHERE utilisateur_id=?
    ORDER BY id DESC
    """,
    (session["user_id"],)
)
    depenses = cursor.fetchall()

    cursor.execute(
    """
    SELECT SUM(montant)
    FROM depenses
    WHERE utilisateur_id=?
    """,
    (session["user_id"],)
)
    total_depenses = cursor.fetchone()[0] or 0

    cursor.execute(
    """
    SELECT * FROM revenus
    WHERE utilisateur_id=?
    ORDER BY id DESC
    """,
    (session["user_id"],)
)

    revenus = cursor.fetchall()

    cursor.execute("""
         SELECT SUM(montant)
         FROM revenus
         WHERE utilisateur_id=?
    """,
    (session["user_id"],)
    )
    total_revenus = cursor.fetchone()[0] or 0

    solde = total_revenus - total_depenses

    conn.close()

    return render_template(
        "dashboard.html",
        nom=session["user_nom"],
        depenses=depenses,
        total_depenses=total_depenses,
        total_revenus=total_revenus,
        solde=solde,
        revenus=revenus
    )
@app.route("/logout")
def logout():


    session.clear()

    return redirect("/")

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
