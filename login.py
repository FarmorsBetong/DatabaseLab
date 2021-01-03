from flask import Blueprint, render_template, render_template, session, flash, redirect,url_for, request
from MySQL import mysql

conn = mysql.connect()

loginfile = Blueprint("loginfile", __name__ , static_folder="static" , template_folder="template")




@loginfile.route('/login', methods = ['GET', 'POST']) #Made by Johan
def login():
    if(request.method == 'POST'):
        if(request.form.get("register")):
            return redirect(url_for("register"))

        email = request.form["email"]
        pwdIn = request.form["pwd"]
        
        #search for the email in the database and extract password
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE email=%s", (email,))
        conn.commit()
        #check password
        rv = cur.fetchone()
        #if the email does not exist
        if(rv == None):
            return redirect(url_for("login"))
        pwdDB = str(rv[0])
        if(pwdDB != pwdIn):
            return "Incorrect login"

        #if the password is correct, we return the login email
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        conn.commit()
        user = cur.fetchall()[0]
        session["user"] = user[0]
        session['name'] = user[1]
        session['surname'] = user[2]
        session['email'] = user[3]
        session['role'] = user[5]
        session["money"] = user[6]

        cur.close()

        return redirect('/')

    return render_template('login.html')

@loginfile.route('/logout')
def logout():
    name = session["name"]
    session.clear()
    flash("You successfully logged out from: " + name, "info")
    return redirect(url_for("index"))

@loginfile.route('/register', methods = ['GET', 'POST']) 
def register():
    if(request.method == 'POST'):
        #Get all the information from the forms
        name = request.form["name"]
        surname = request.form["surname"]
        email = request.form["Email_input"]
        password = request.form["Pass_input"]
        password2 = request.form["Pass_input2"]

        cur = conn.cursor()
        query = "SELECT email FROM users;" #bättre query, säker //Johan
        cur.execute(query)
        conn.commit()
        allEmails = cur.fetchall()
        for emails in allEmails:
            if email == emails[0]:
                flash("Email: " + email + " already exists", "error")
                return redirect(url_for("register"))

        if(password == password2):  
            query = "INSERT INTO users VALUES (NULL, '%s', '%s', '%s', '%s','user','0', 'NULL');" %(name, surname, email, password) #bättre query, säker //Johan
            cur.execute(query)
            conn.commit()
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            conn.commit()
            user = cur.fetchall()[0]
            cur.close()
            session["user"] = user[0]
            session['name'] = user[1]
            session['surname'] = user[2]
            session['email'] = user[3]
            session['role'] = user[5]
            session['money'] = user[6]
            return redirect('/')
        else:
            flash("Thats not the same password...", "info")
            return redirect(url_for("register"))

        cur.close()
    return render_template('register.html')
