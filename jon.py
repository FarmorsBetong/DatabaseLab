from flask import Flask, render_template, request, redirect,url_for, session
from flaskext.mysql import MySQL
from flask_login import LoginManager
from datetime import datetime


app = Flask(__name__)
app.secret_key = "robinsnyckel"

mysql = MySQL()
mysql.init_app(app)


app.config['MYSQL_DATABASE_PASSWORD'] = 'robin123'
app.config['MYSQL_DATABASE_DB'] = 'test'
app.config['MYSQL_DATABASE_USER'] = 'root'
conn = mysql.connect()
# Create tables
def createTables():  #<-- bättre att ha ne funktion för att göra tables //Johan
    cur = mysql.connect().cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users(
        userID INT UNSIGNED AUTO_INCREMENT NOT NULL,
        firstname VARCHAR(100) NOT NULL,
        surname VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        password VARCHAR(100) NOT NULL,
        role VARCHAR(10) NOT NULL,
        PRIMARY KEY(userID))
        ''')
                    
    cur.execute('''CREATE TABLE IF NOT EXISTS article(
        article_number INT UNSIGNED AUTO_INCREMENT NOT NULL,
        article_name VARCHAR(100) NOT NULL,
        price INT NOT NULL,
        amount INT NOT NULL,
        PRIMARY KEY(article_number))
        ''')

    cur.execute('''CREATE TABLE IF NOT EXISTS orders(
        order_number INT UNSIGNED AUTO_INCREMENT NOT NULL,
        userID INT UNSIGNED NOT NULL,
        datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        order_placed BOOLEAN DEFAULT FALSE NOT NULL,
        PRIMARY KEY(order_number),
        FOREIGN KEY(userID) REFERENCES users(userID)
        )''')
            
    cur.execute('''CREATE TABLE IF NOT EXISTS booked_items(
        order_number INT UNSIGNED NOT NULL,
        article_number INT UNSIGNED NOT NULL,
        amount INT UNSIGNED NOT NULL,
        FOREIGN KEY(order_number) REFERENCES orders(order_number) ON DELETE CASCADE,
        FOREIGN KEY(article_number) REFERENCES article(article_number)
        )''')
            
    cur.execute('''CREATE TABLE IF NOT EXISTS opinion(
        article_number INT UNSIGNED NOT NULL,
        userID INT UNSIGNED NOT NULL,
        grade INT,
        comment VARCHAR(200),
        FOREIGN KEY(order_number) REFERENCES users(userID),
        FOREIGN KEY(article_number) REFERENCES article(article_number)
        )''')
    conn.commit()
    cur.close()
    return

@app.route('/', methods = ['GET', 'POST'])
def index():
    if(request.method == "POST"):
       text = request.form["searchbtn"] #bara lite exempel på hur man tar input från html search lådan
       return redirect(url_for("search"))
    return render_template('index.html')

@app.route('/search', methods = ['GET', 'POST']) #Search page to look for items in database.
def search():
    if(request.method == "POST"):
        text = request.form["searchArticle"]
        #cur = conn.cursor()
        #cur.execute("SELECT * FROM article WHERE article_name = %s",text)
        #rv = cur.fetchall()
        #cur.close()
        return redirect(url_for("searchResult", res = text))

    return render_template('search.html')


@app.route('/search/<string:res>', methods = ['GET', 'POST'])
def searchResult(res):
    cur = conn.cursor()
    cur.execute("SELECT * FROM article WHERE article_name = %s",res)
    rv = cur.fetchall()[0]
    print(rv)
    cur.close()



    return render_template('searchResult.html',test = rv, search = res)



@app.route('/admin', methods = ['GET', 'POST']) #admin page to add items to the database
def admin():
    if(request.method == "POST"):
        cur = conn.cursor()
        query = request.form["configure"]
        cur.execute(query)
        conn.commit()
        cur.close()

    return render_template('admin.html')


@app.route('/login', methods = ['GET', 'POST']) #Made by Johan
def login():
    if(request.method == 'POST'):
        email = request.form["email"]
        pwdIn = request.form["pwd"]
        
        #search for the email in the database and extract password
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE email=%s", (email,))
        conn.commit()

        #check password
        temp = cur.fetchone()
        #if the email does not exist
        if(temp == None):
            return "No user with that email"
        pwdDB = str(temp[0])
        if(pwdDB != pwdIn):
            return "Incorrect login"

        #if the password is correct, we return the login email
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        conn.commit()
        user = cur.fetchall()[0]
        #user = str(cur.fetchone()[0])
        #name = str(cur.fetchone())
        #session['name'] = str(cur.fetchone()[1])
        session["user"] = user[0]
        session['name'] = user[1]
        session['surname'] = user[2]

        cur.close()

        return redirect('/')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return render_template('logout.html')

@app.route('/register', methods = ['GET', 'POST']) #Modified by Johan
def register():
    if(request.method == 'POST'):

        #Get all the information from the forms
        name = request.form["name"]
        surname = request.form["surname"]
        email = request.form["Email_input"]
        password = request.form["Pass_input"]
        password2 = request.form["Pass_input2"]
        
        
        if(password == password2):  
            cur = conn.cursor()
            query = "INSERT INTO users VALUES (NULL, '%s', '%s', '%s', '%s','user');" %(name, surname, email, password) #bättre query, säker //Johan
            #query = "INSERT INTO users VALUES (NULL,'" + name + "' ,'" + surname + "', '" + email + "','" + password + "','user');"
            cur.execute(query)
            conn.commit()
            cur.close()
            return redirect(url_for("success"))
        else:
            return "Thats not the same password..."
    return render_template('register.html')

@app.route('/success', methods = ['GET', 'POST']) 
def success():
    return render_template('success.html')


@app.route('/varukorg', methods = ['GET', 'POST']) 
def varukorg():
    return render_template('varukorg.html')



@app.route('/add_to_cart/<int:articleNum>', methods = ['GET', 'POST'])
def add_to_cart(articleNum):
    # Kolla om användaren är inloggad, annars skicka dem till inloggningen.
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))
    
    cur = conn.cursor()

    # Kolla om det finns en aktiv varukorg till användaren.
    query = "SELECT * FROM orders WHERE userID='%s' AND order_placed=0;" %(user)
    cur.execute(query)
    conn.commit()
    responce = str(cur.fetchone())
    if responce == "None":
        timeStamp = datetime.now()
        timeStamp = str(timeStamp.year) + str(timeStamp.month) + str(timeStamp.day)
        
        # Skapa en ny aktiv order.
        query = "INSERT INTO orders VALUES(null, '%s', '%s', 0);" %(user, timeStamp)
        cur.execute(query)
        conn.commit()

    # Hämta det aktiva order numret för användaren.
    query = "SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0;" %(user)
    cur.execute(query)
    conn.commit()
    orderNum = str(cur.fetchone()[0])
    
    # Kolla om samma vara redan finns i aktiv varukorg.
    query = "SELECT amount FROM booked_items WHERE order_number='%s' AND article_number='%s';" %(orderNum, articleNum)
    cur.execute(query)
    conn.commit()
    amount = str(cur.fetchone())
    
    if amount == "None":
        # Lägg till vara till ordern.
        query = "INSERT INTO booked_items VALUES('%s', '%s', 1);" %(orderNum, articleNum)
        cur.execute(query)
        conn.commit()
    else:
        # Om varan redan finns updatera amount av varan.
        query = "UPDATE booked_items SET amount='%s' WHERE order_number='%s' AND article_number='%s';" %(str(int(amount[1])+1), orderNum, articleNum)
        cur.execute(query)
        conn.commit()

    cur.close()
    return redirect("/")
    
@app.route('/profile', methods = ['GET', 'POST'])
def profile():
    return render_template('profile.html')

# Om man vill minska antal av en vara updaterar man amount av varan.
@app.route('/lower_amount/<int:id>', methods = ['GET', 'POST'])
def lower_amount(id):
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))
    
    cur = conn.cursor()

    query = "SELECT amount FROM booked_items where article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(id,user)
    #return query
    cur.execute(query)
    conn.commit()
    amount = cur.fetchone()[0]

    # Varan kan inte bli mindre än 1
    if amount > 1:
        amount = amount - 1
        query = "UPDATE booked_items SET amount='%i' WHERE article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(amount,id,user)
        cur.execute(query)
        conn.commit()

    cur.close()
    return redirect(url_for("varukorg"))

# Om man trycker på ta bort så tas varan bort från varukorgen.
@app.route("/remove_from_order/<int:id>", methods = ['GET', 'POST'])
def remove_from_order(id):
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))
    
    cur =conn.cursor()

    query = "DELETE FROM booked_items WHERE article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(id,user)
    cur.execute(query)
    conn.commit()

    cur.close()
    return redirect(url_for("varukorg"))


if __name__ == '__main__':
    createTables()
    app.debug = True
    app.run(host = '0.0.0.0')
