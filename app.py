from flask import Flask, render_template, request, redirect,url_for, session, flash
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
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(100) NOT NULL,
        role VARCHAR(10) NOT NULL,
        money INT NOT NULL DEFAULT '0',
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
        if(request.form.get("info_btn")):
            artID = request.form['info_btn']
            return redirect(url_for("itemInfo", artID = artID))
        else:
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
            return redirect(url_for("itemInfo", artID = artID))
        else:
            text = request.form["searchArticle"]
            return redirect(url_for("searchResult", res = text))


    cur = conn.cursor()
    cur.execute("SELECT * FROM articles WHERE article_name = %s",res)
    conn.commit()
    rv = cur.fetchall()
    cur.close()

    #lägg till och ta bort specifik vara ur varukorg från search sidan
    #print(rv)  

    return render_template('searchResult.html',products = rv, search = res)



def confirmOrder(): #bekräfta ordern

    cur = conn.cursor()
    user = session["user"]
    cur.execute("SELECT article_number, amount FROM booked_items WHERE order_number = (SELECT order_number FROM orders WHERE userID=%s AND order_placed = 0)",user)
    conn.commit()
    articles = cur.fetchall()
    print(articles)
    if(len(articles) == 0):
        return
    cur.execute("UPDATE orders SET order_placed = 1 WHERE userID = %s AND order_placed = 0",user)
    for artPair in articles:
        art = artPair[0]
        amount = artPair[1]

        cur.execute("UPDATE articles SET amount = amount - %s WHERE article_number = %s",(amount, art))


    conn.commit()

    #transaction(user, )


    cur.close()
    return

def removeOrder(ordNum): #ta bort en befintlig order
    cur = conn.cursor()
    user = session["user"]
    cur.execute("DELETE FROM orders WHERE userID = %s AND order_number = %i"%(user, ordNum))
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

@app.route('/logout')
def logout():
    name = session["name"]
    session.clear()
    flash("You successfully logged out from: " + name, "info")
    return redirect(url_for("index"))

@app.route('/register', methods = ['GET', 'POST']) 
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
        print("Kolla här\n")
        for emails in allEmails:
            if email == emails[0]:
                flash("Email: " + email + " already exists", "error")
                return redirect(url_for("register"))

        if(password == password2):  
            query = "INSERT INTO users VALUES (NULL, '%s', '%s', '%s', '%s','user','0');" %(name, surname, email, password) #bättre query, säker //Johan
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
            return render_template("index.html")
        else:
            flash("Thats not the same password...", "info")
            return redirect(url_for("register"))
    return render_template('register.html')

# varukorgen
@app.route('/varukorg', methods = ['GET', 'POST']) 
def varukorg():       
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))

    if(request.method == 'POST'):
        #print(request.form.get("confirmOrderBtn"))
        if(request.form.get("addBtn")):
            artID = int(request.form["addBtn"])
            #print(artID)
            add_to_cart(artID,user)
        elif(request.form.get("removeBtn")):
            artID = int(request.form["removeBtn"])
            lower_amount(artID,user)
        elif(request.form.get("confirmOrderBtn")):
            cur = conn.cursor()
            query = "SELECT order_number FROM orders WHERE userID='%i' AND order_placed=0;" %(user)
            cur.execute(query)
            conn.commit()
            orders = cur.fetchone()
            if(orders != None):
                orderNr = orders[0]
            
                query = "SELECT articles.article_number, articles.article_name, articles.price, booked_items.amount FROM booked_items INNER JOIN articles ON booked_items.article_number=articles.article_number WHERE booked_items.order_number='%i';" %(orderNr)
                cur.execute(query)
                conn.commit()
                allOrders = cur.fetchall()
            
                amount = 0
                for x in allOrders:
                    amount += x[2] * x[3]
        
                cur.close()
                if(transaction(user, amount)):
                    confirmOrder()
        else:
            text = request.form["searchbtn"] 
            return redirect(url_for("searchResult", res = text))

    # Get the users order number for the active basket.
    cur = conn.cursor()
    query = "SELECT order_number FROM orders WHERE userID='%i' AND order_placed=0;" %(user)
    cur.execute(query)
    conn.commit()
    orders = cur.fetchone()
    if(orders != None):
        orderNr = orders[0]
    
        query = "SELECT articles.article_number, articles.article_name, articles.price, booked_items.amount FROM booked_items INNER JOIN articles ON booked_items.article_number=articles.article_number WHERE booked_items.order_number='%i';" %(orderNr)
        cur.execute(query)
        conn.commit()
        allOrders = cur.fetchall()
    
        total = 0
        for x in allOrders:
            total += x[2] * x[3]
   
        cur.close()
        return render_template('/varukorg.html', infoAboutItems = allOrders, totalPrice = total)

    cur.close()
    return render_template('/varukorg.html', infoAboutItems = (), totalPrice = 0)

def add_to_cart(articleNum, user):
    cur = conn.cursor()
    # Kolla om det finns en aktiv varukorg till användaren.
    query = "SELECT * FROM orders WHERE userID='%s' AND order_placed=0;" %(user)
    cur.execute(query)
    conn.commit()
    response = cur.fetchone()
    if (response == None):
        timeStamp = datetime.now()
        if(timeStamp.day < 10):
            timeStamp = str(timeStamp.year) + str(timeStamp.month) + "0" + str(timeStamp.day)#måste vara i format YYYYMMDD där dagen är t.ex 27 eller 08, därav nollan just nu
        else:
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
    amount = cur.fetchone()
    
    if (amount == None):
        query = "SELECT amount FROM articles WHERE article_number = %s;"%(articleNum)
        cur.execute(query)
        conn.commit()
        rv = cur.fetchone()
        if(rv[0] == 0):
            cur.close() 
            return 

        # Lägg till vara till ordern.
        query = "INSERT INTO booked_items VALUES('%s', '%s', 1);" %(orderNum, articleNum)
        cur.execute(query)
        conn.commit()
    else:
        query = "SELECT amount FROM articles WHERE article_number = %s;"%(articleNum)
        cur.execute(query)
        conn.commit()
        rv = cur.fetchone()
        #ifall antalet artiklar på hyllan kommer underskrida antalet i varukorgen skall antalet ej öka
        if(amount[0] + 1 > rv[0]):
            cur.close()
            return 
        # Om varan redan finns updatera amount av varan.
        query = "UPDATE booked_items SET amount='%s' WHERE order_number='%s' AND article_number='%s';" %(str((amount[0])+1), orderNum, articleNum)
        cur.execute(query)
        conn.commit()

    cur.close()
    return 
    


# Om man vill minska antal av en vara updaterar man amount av varan.
#@app.route('/lower_amount/<int:id>', methods = ['GET', 'POST'])
def lower_amount(id, user):
    cur = conn.cursor()
    query = "SELECT amount FROM booked_items where article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(id,user)
    cur.execute(query)
    conn.commit()
    amount = cur.fetchone()
    if (amount == None):
        return

    amount = amount[0]
    #print(amount)
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
def remove_from_order(artID,user):
    cur = conn.cursor()
    query = "DELETE FROM booked_items WHERE article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(artID,user)
    cur.execute(query)
    conn.commit()

    cur.close()
    return #redirect(url_for("varukorg"))



#@app.route('/addGrade/<int:artID>/<int:userID>/<int:grade>')
def addGrade(artID, userID, grade):
    cur = conn.cursor()
    query = "SELECT * FROM opinion WHERE article_number = '%i' AND userID = '%i';"%(artID, userID)
    cur.execute(query)
    conn.commit()

    if(cur.fetchone() == None):
        query = "INSERT INTO opinion VALUES('%i', '%i', '%i', NULL);"%(artID, userID, grade)
        cur.execute(query)
        
        
    else: 
        query = "UPDATE opinion SET grade = '%i' WHERE article_number = '%i' AND userID='%i';"%(grade, artID, userID)
        cur.execute(query)

    conn.commit()
    cur.close()
    return 



#@app.route('/add_comment/<int:articleID>/<int:userID>/<string:comment>')
def addComment(articleID, userID, comment):
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
    return #redirect(url_for("index"))#här ska den redirecta tillbaka till artikelsidan.

@app.route('/item/<int:artID>', methods = ['GET', 'POST'])
def itemInfo(artID):

    if(request.method == 'POST'):
        if("user" in session):
            user = session["user"]
        else:
            return redirect(url_for("login"))

        if(request.form.get("reviewBtn")):
            comment = str(request.form["commentBox"])
            grade = int(request.form["gradeBox"])
            user = session["user"]

            addComment(artID,user,comment)
            addGrade(artID,user,grade)

            print(comment + ", " + str(grade))
        elif(request.form.get("addBtn")):
                        
            artID = int(request.form["addBtn"])
            print(artID)
            print(user)
            add_to_cart(artID,user)
        else:
            text = request.form["searchbtn"]
            return redirect(url_for("searchResult", res = text))
        


    cur = conn.cursor()
    query = "SELECT * FROM articles WHERE article_number = %s;"%(artID)
    cur.execute(query)
    conn.commit()
    product = cur.fetchone()

    query = "SELECT * FROM opinion WHERE article_number = %s;"%(artID)
    cur.execute(query)
    conn.commit()
    grades = cur.fetchall()

    gradeSum = 0
    for grade in grades:
        if(grade[2] == None):
            continue
        gradeSum = gradeSum + grade[2]
    if(len(grades) == 0):
        gradeAvg = 0
    else:
        gradeAvg = gradeSum/len(grades)
    cur.close()
    return render_template("itemInfo.html", product = product, grades = grades, gradeAvg = gradeAvg)


def transaction(looser,amount):
    gainer = 24
    cur = conn.cursor()
    try:
        query = "START TRANSACTION"
        cur.execute(query)

        query = "UPDATE users SET money = money - %i WHERE userID = %s"%(amount, looser)#someone looses money
        cur.execute(query)

        query = "UPDATE users SET money = money + %i WHERE userID = %s"%(amount, gainer)#the bank gains money
        cur.execute(query)

        conn.commit()
        cur.close()
        return True
    except:
        conn.rollback()
        cur.close()
        return False
    

def addMoney(amount, user):
    cur = conn.cursor()
    query = "UPDATE users SET money = money + %i WHERE userID = %s"%(amount, user)
    cur.execute(query)
    conn.commit()
    cur.close()
    return


def removeMoney(amount, user):
    cur = conn.cursor()
    query = "SELECT money FROM users WHERE userID = %s"%(user)
    cur.execute(query)
    conn.commit()
    currAmount = cur.fetchone()
    #if the users lacks sufficient funds
    if(amount > currAmount[0]):
        return
    query = "UPDATE users SET money = money - %i WHERE userID = %s"%(amount, user)
    cur.execute(query)
    conn.commit()
    cur.close()
    return
    

# -----------      Profile routes --------------

@app.route('/profile', methods = ['GET', 'POST'])
def profile():
    #
    #om ens user-role är admin bör en adminsida returneras istället
    #
    cur = conn.cursor()
    

    if(request.method == 'POST'):
        if(request.form.get("submitUser")):
            fname = request.form["fname"]
            lname = request.form["lname"]
            email = request.form["email"]
            query = "UPDATE users SET firstname = '%s', surname = '%s', email = '%s' WHERE userID ='%s'" %(fname,lname,email,session['user'])
            cur.execute(query)
            conn.commit()
            session['name'] = fname
            session['surname'] = lname
        elif(request.form.get("addMoneyBtn")):
            amount = int(request.form["makeMoney"])

            if(amount > 0):
                addMoney(amount,session["user"])
            else:
                amount = -amount
                removeMoney(amount,session["user"])
                session['money'] = amount
        elif(request.form.get("submitPass")):
            request.form['Password']
            oldPass = request.form['Password']
            newPass = request.form['newPassword']
            newPassAgain = request.form['newPasswordAgain']
            print("hallå")
            query = "SELECT users.password FROM users WHERE userID='%s'" %(session['user'])
            cur.execute(query)
            conn.commit()
            currentPass = cur.fetchone()[0]
            print(currentPass)

            if(currentPass == oldPass):
                if(newPass == newPassAgain):
                    print("kommer vi hit?")
                    query = "UPDATE users SET password = '%s' WHERE userID ='%s'" %(newPass,session['user'])
                    cur.execute(query)
                    conn.commit()
                else:
                    flash("The password doesn't match!")
            else:
                flash("You entered the wrong password!")

    query = "Select users.firstname, users.surname, users.email, users.money from users where userID='%i'" %(session['user'])
    cur.execute(query)
    conn.commit()
    userinfo = cur.fetchone()
    cur.close()
    return render_template('profile.html', userInfo = userinfo)


@app.route('/profile/orders', methods = ['GET', 'POST'])
def profileOrders():
    cur = conn.cursor()
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))

    if(request.method == 'POST'):
        ordNr = int(request.form['remove_order'])
        removeOrder(ordNr)

    query = "SELECT order_number FROM orders WHERE userID='%i' AND order_placed=1;" %(user)
    cur.execute(query)
    conn.commit()
    orderNr = cur.fetchall()


    orders = []
    total = 0
    totalAmountOrders =  []
    for orderNum in orderNr:
        #orders.append(orderNum[0])
        query = "SELECT articles.article_number, articles.article_name, articles.price, booked_items.amount, booked_items.order_number FROM booked_items INNER JOIN articles ON booked_items.article_number=articles.article_number WHERE booked_items.order_number='%i';" %(orderNum[0])
        cur.execute(query)
        conn.commit()
        order = cur.fetchall()
        orders.append(order)

        # Calulate the total price of one order.
        
        for item in order:
            total += item[2] * item[3]
        totalAmountOrders.append(total)
        total = 0

    


    return render_template('profileOrders.html', orders = orders, totalPrice = totalAmountOrders)
    
@app.route('/overview', methods = ['GET', 'POST'])
def overview():
    cur = conn.cursor()
    query = "Select * from users where role='user';"
    cur.execute(query)
    conn.commit()
    users = cur.fetchall()
    return render_template('overview.html', users = users)


if __name__ == '__main__':
    createTables()
    app.debug = True
    app.run(host = '0.0.0.0')
