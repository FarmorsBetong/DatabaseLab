from flask import Flask, render_template, request, redirect,url_for, session
from flaskext.mysql import MySQL
from flask_login import LoginManager
from datetime import datetime


app = Flask(__name__)
app.secret_key = "robinsnyckel"

mysql = MySQL()
mysql.init_app(app)


app.config['MYSQL_DATABASE_PASSWORD'] = 'robin123'
app.config['MYSQL_DATABASE_DB'] = 'ecommerce'
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
                    
    cur.execute('''CREATE TABLE IF NOT EXISTS articles(
        article_number INT UNSIGNED AUTO_INCREMENT NOT NULL,
        article_name VARCHAR(100) NOT NULL,
        price INT NOT NULL,
        amount INT NOT NULL,
        info VARCHAR(200) NOT NULL,
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
        FOREIGN KEY(article_number) REFERENCES articles(article_number)
        )''')
            
    cur.execute('''CREATE TABLE IF NOT EXISTS opinion(
        article_number INT UNSIGNED NOT NULL,
        userID INT UNSIGNED NOT NULL,
        grade INT,
        comment VARCHAR(200),
        FOREIGN KEY(userID) REFERENCES users(userID),
        FOREIGN KEY(article_number) REFERENCES articles(article_number)
        )''')
    conn.commit()
    cur.close()
    return

@app.route('/', methods = ['GET', 'POST'])
def index():
    if(request.method == "POST"):
       text = request.form["searchbtn"] #bara lite exempel på hur man tar input från html search lådan
       return redirect(url_for("searchResult", res = text))
    
    cur = conn.cursor()
    query = "SELECT * FROM articles"
    cur.execute(query)
    conn.commit()
    items = cur.fetchall()
       

    return render_template('index.html', items = items)

@app.route('/search', methods = ['GET', 'POST']) #Search page to look for items in database.
def search():
    if(request.method == "POST"):
        text = request.form["searchArticle"]
        return redirect(url_for("searchResult", res = text))

    return render_template('search.html')


@app.route('/search/<string:res>', methods = ['GET', 'POST'])
def searchResult(res):
    if(request.method == "POST"):
        if "user" in session:
            user = session["user"]
        else:
            return redirect(url_for("login"))

        if(request.form.get("addBtn")):
            artID = int(request.form["addBtn"])
            add_to_cart(artID,user)
        elif(request.form.get("removeBtn")):
            artID = int(request.form["removeBtn"])
            lower_amount(artID,user)
        elif(request.form.get("itemInfo")):
            artID = int(request.form["itemInfo"])
            return redirect(url_for("itemPage", item = artID))
        else:
            text = request.form["searchArticle"]
            return redirect(url_for("searchResult", res = text))


    cur = conn.cursor()
    cur.execute("SELECT * FROM articles WHERE article_name = %s",res)
    conn.commit()
    rv = cur.fetchall()
    cur.close()

    #lägg till och ta bort specifik vara ur varukorg från search sidan
      

    return render_template('searchResult.html',products = rv, search = res)



def confirmOrder(): #bekräfta ordern
    cur = conn.cursor()
    user = session["user"]
    cur.execute("UPDATE orders SET order_placed = 1 WHERE userID = %s AND order_placed = 0",user)
    #
    #Måste minska antalet varor i "hyllan" också
    #
    #
    conn.commit()
    cur.close()
    return

def removeOrder(ordNum): #ta bort en befintlig order
    cur = conn.cursor()
    user = session["user"]
    cur.execute("DELETE FROM orders WHERE userID = %s AND order_number = %i",(user, ordNum))
    conn.commit()
    cur.close()
    return

@app.route('/admin', methods = ['GET', 'POST']) #admin page to add items to the database
def admin():
    if 'role' in session:
        if session['role'] == 'admin':
            return render_template('admin.html')
        else:
            return "Ge fan i att försöka ta dig till fking admin asså"
            # return render_template('profile.html')
    return "Ge fan i att försöka ta dig till fking admin asså"

    


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
        rv = cur.fetchone()
        #if the email does not exist
        if(rv == None):
            return "No user with that email"
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
        session['role'] = user[5]

        cur.close()

        return redirect('/')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return render_template('logout.html')

@app.route('/register', methods = ['GET', 'POST']) 
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
            cur.execute(query)
            conn.commit()
            cur.close()
            return render_template("success.html")
        else:
            return "Thats not the same password..."
    return render_template('register.html')


@app.route('/varukorg', methods = ['GET', 'POST']) 
def varukorg():       
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))

    if(request.method == 'POST'):
        print(request.form.get("confirmOrderBtn"))
        if(request.form.get("addBtn")):
            artID = int(request.form["addBtn"])
            add_to_cart(artID,user)
        elif(request.form.get("removeBtn")):
            artID = int(request.form["removeBtn"])
            lower_amount(artID,user)
        elif(request.form.get("confirmOrderBtn")):
            confirmOrder()
        else:
            text = request.form["searchbtn"] #bara lite exempel på hur man tar input från html search lådan
            return redirect(url_for("searchResult", res = text))

    
    cur = conn.cursor()
    query = "SELECT * FROM booked_items WHERE order_number=(SELECT order_number FROM orders WHERE userID='%i' AND order_placed=0);" %(user)
    cur.execute(query)
    conn.commit()
    items = cur.fetchall()
    
    total = 0
    for article in items:
        query = "SELECT price FROM articles WHERE article_number='%i'" %(article[1])
        cur.execute(query)
        conn.commit()
        price = cur.fetchone()
        total = total + (price[0]*article[2])
    
    cur.close() 
    return render_template('/varukorg.html', infoAboutItems = items, total = total)


def add_to_cart(articleNum, user):
    cur = conn.cursor()

    # Kolla om det finns en aktiv varukorg till användaren.
    query = "SELECT * FROM orders WHERE userID='%s' AND order_placed=0;" %(user)
    cur.execute(query)
    conn.commit()
    response = cur.fetchone()
    if (response == None):
        timeStamp = datetime.now()
        timeStamp = str(timeStamp.year) + str(timeStamp.month) + "0" + str(timeStamp.day)#måste vara i format YYYYMMDD där dagen är t.ex 27 eller 08, därav nollan just nu
        
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
    amount = cur.fetchone()
    
    if amount == None:
        # Lägg till vara till ordern.
        query = "INSERT INTO booked_items VALUES('%s', '%s', 1);" %(orderNum, articleNum)
        cur.execute(query)
        conn.commit()
    else:
        # Om varan redan finns updatera amount av varan.
        query = "UPDATE booked_items SET amount='%s' WHERE order_number='%s' AND article_number='%s';" %(str((amount[0])+1), orderNum, articleNum)
        cur.execute(query)
        conn.commit()

    cur.close()
    return 
    
@app.route('/profile', methods = ['GET', 'POST'])
def profile():
    return render_template('profile.html')

# Om man vill minska antal av en vara updaterar man amount av varan.
@app.route('/lower_amount/<int:id>', methods = ['GET', 'POST'])
def lower_amount(id, user):
    cur = conn.cursor()
    query = "SELECT amount FROM booked_items where article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(id,user)
    cur.execute(query)
    conn.commit()
    amount = cur.fetchone()
    if (amount == None):
        return

    amount = amount[0]
    print(amount)
    # Varan kan inte bli mindre än 0
    if amount > 0:
        amount = amount - 1
        query = "UPDATE booked_items SET amount='%i' WHERE article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(amount,id,user)
        cur.execute(query)
        conn.commit()
    if amount == 0:
        remove_from_order(id,user)
    
    cur.close()
    return redirect(url_for("varukorg"))

# Om man trycker på ta bort så tas varan bort från varukorgen.
def remove_from_order(id,user):
    cur = conn.cursor()
    query = "DELETE FROM booked_items WHERE article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(id,user)
    cur.execute(query)
    conn.commit()

    cur.close()
    return redirect(url_for("varukorg"))

@app.route('/add_comment/<int:articleID>/<int:userID>/<string:comment>')
def add_comment(articleID, userID, comment):
    cur = conn.cursor()
    query = "SELECT * FROM opinion WHERE article_number='%i' AND userID='%i';" %(articleID, userID)
    cur.execute(query)
    conn.commit()

    if cur.fetchone() == None:
        query = "INSERT INTO opinion VALUES('%i', '%i', NULL, '%s');" %(articleID, userID, comment)
        cur.execute(query)
        conn.commit()
    else:
        query = "UPDATE opinion SET comment='%s' WHERE article_number='%i' AND userID='%i';" %(comment, articleID, userID)
        cur.execute(query)
        conn.commit()
    return redirect(url_for("index"))#här ska den redirecta tillbaka till artikelsidan.

#@app.route('/item_info')

if __name__ == '__main__':
    createTables()
    app.debug = True
    app.run(host = '0.0.0.0')
