from flask import Flask, render_template, request, redirect,url_for, session, flash, send_file
from flaskext.mysql import MySQL
from datetime import datetime
import os

class NotEnoughItemsInCart(Exception): #custom exceptions
    pass

class NotEnoughItemsInStock(Exception):
    pass

app = Flask(__name__)
app.secret_key = "robinsnyckel"

#app.register_blueprint(MySQL, url_prefix="")

mysql = MySQL()


mysql.init_app(app)


app.config['MYSQL_DATABASE_PASSWORD'] = 'robin123'
app.config['MYSQL_DATABASE_DB'] = 'ecommerce'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config["USER_IMAGE_UPLOADS"] = "/home/johansnurre/databasprojekt/static/images/userImages"
#config routen för att spara artikle bilderna
app.config["ARTICLE_IMAGE_UPLOADS"] = "/home/johansnurre/databasprojekt/static/images/articles"



#Link your blueprints and specify when you want to access it    
#app.register_blueprint(loginfile, url_prefix="/userAuthincation")

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
        user_img VARCHAR(100),
        PRIMARY KEY(userID))
        ''')
 
    # +-------------------------------articles--------------------------------+                
    # +----------------+--------------+------+-----+---------+----------------+
    # | Field          | Type         | Null | Key | Default | Extra          |
    # +----------------+--------------+------+-----+---------+----------------+
    # | article_number | int unsigned | NO   | PRI | NULL    | auto_increment |
    # | article_name   | varchar(100) | NO   |     | NULL    |                |
    # | price          | int          | NO   |     | NULL    |                |
    # | amount         | int          | NO   |     | NULL    |                |
    # | info           | varchar(200) | YES  |     | NULL    |                |
    # +----------------+--------------+------+-----+---------+----------------+
    cur.execute('''CREATE TABLE IF NOT EXISTS articles(
        article_number INT UNSIGNED AUTO_INCREMENT NOT NULL,
        article_name VARCHAR(100) NOT NULL,
        price INT NOT NULL,
        amount INT NOT NULL,
        info VARCHAR(200) NOT NULL,
        image_name VARCHAR(100) NOT NULL,
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
        price INT UNSIGNED NOT NULL,
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


#------------------Routes-------------------#

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
    cur.close()

    return render_template('index.html', items = items)


@app.route('/search', methods = ['GET', 'POST']) #Search page to look for items in database.
def search():
    if(request.method == "POST"):
        text = request.form["searchArticle"]
        return redirect(url_for("searchResult", res = text))

    return render_template('search.html')


@app.route('/search/<string:res>', methods = ['GET', 'POST'])
def searchResult(res): #made by Johan
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

    return render_template('searchResult.html',products = rv, search = res)


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
        query = "SELECT email FROM users;" 
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


# varukorgen
@app.route('/varukorg', methods = ['GET', 'POST']) 
def varukorg():       
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))

    if(request.method == 'POST'):
       
        if(request.form.get("addBtn")):
            artID = int(request.form["addBtn"])
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
                #+----------------+--------------+-------+--------+
                #| article_number | article_name | price | amount | detta är allOrders
                #+----------------+--------------+-------+--------+

                amount = 0
                for order in allOrders:
                    amount += order[2] * order[3]
                    query = "UPDATE booked_items set price = '%i' WHERE order_number = '%s' AND article_number='%s';"%(order[2],orderNr,order[0])
                    cur.execute(query)
                    conn.commit() 
                cur.close()

                if(sufficientFunds(amount, user)):# Is there enough money? #made by Johan
                    cur = conn.cursor()
                    cur.execute("SELECT booked_items.article_number, booked_items.amount, articles.amount FROM booked_items,articles WHERE order_number = (SELECT order_number FROM orders WHERE userID=%s AND order_placed = 0) AND booked_items.article_number = articles.article_number",user)
                    conn.commit()
                    articles = cur.fetchall()
                    
                    try:
                        query = "START TRANSACTION"
                        cur.execute(query)

                        if(len(articles) == 0):
                            raise NotEnoughItemsInCart("Not enough articles in shopping basket")

                        query = "UPDATE users SET money = money - %s WHERE userID = %s"%(amount, user)#someone looses money
                        cur.execute(query)
                        query = "UPDATE users SET money = money + %s WHERE userID = %s"%(amount, 24)#someone gains money
                        cur.execute(query)
                
                        
                    #check so that there are enough items in stock
                        for article in articles:
                            if(article[1] > article[2]):
                                raise NotEnoughItemsInStock("Not enough artices in stock")           #if there are not enough items in stock, return False

                        #lower the amount on those rows
                        for article in articles:
                            cur.execute("UPDATE articles SET articles.amount = articles.amount - %s WHERE articles.article_number=%s",(article[1], article[0],))
                           
                        #make order_placed = 1
                        cur.execute("UPDATE orders SET order_placed = 1 WHERE userID = %s AND order_placed = 0",user)
                       
                        query = "COMMIT"
                        cur.execute(query)

                        conn.commit()
                        cur.close()

                    except NotEnoughItemsInCart as e:
                        flash(e)
                        conn.rollback()
                        cur.close()
                    except NotEnoughItemsInStock as e:
                        flash(e)
                        conn.rollback()
                        cur.close()

                    except:
                        conn.rollback()
                        cur.close()


                   # if(transaction(user, 24, amount)):  #Can you make a transaction? 24 is the bank userID
                   #     res = confirmOrder()
                   #     if(not res):
                   #         transaction(24, user, amount)#if the order doesn't pull through
                   #         flash("Some item(s) are not in stock, check again")
                   #     elif(res == "Empty"):
                   #         flash("Can't buy an empty cart.")
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
    
        query = "SELECT articles.article_number, articles.article_name, articles.price, articles.image_name, booked_items.amount FROM booked_items INNER JOIN articles ON booked_items.article_number=articles.article_number WHERE booked_items.order_number='%i';" %(orderNr)
        cur.execute(query)
        conn.commit()
        allOrders = cur.fetchall()
    
        total = 0
        for x in allOrders:
            total += x[2] * x[4]
   
        cur.close()
        return render_template('/varukorg.html', infoAboutItems = allOrders, totalPrice = total)

    cur.close()
    return render_template('/varukorg.html', infoAboutItems = (), totalPrice = 0)


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
        elif(request.form.get("addBtn")):            
            artID = int(request.form["addBtn"])
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
        gradeAvg = round(gradeSum/len(grades),2)
    cur.close()
    return render_template("itemInfo.html", product = product, grades = grades, gradeAvg = gradeAvg)



# -----------      Profile routes --------------


@app.route('/profile', methods = ['GET', 'POST'])
def profile():
    #
    #om ens user-role är admin bör en adminsida returneras istället
    #
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))
    cur = conn.cursor()

    if(request.method == 'POST'):
        if(request.form.get("submitUser")):
            fname = request.form["fname"]
            lname = request.form["lname"]
            email = request.form["email"]
            userImg = request.files["inputFile"]
            try:
                if(len(fname) > 100):
                    flash("To long name!")

                if(len(lname) > 100):
                    flash("To long surname!")
                
                if(len(email) > 100):
                    flash("To long email!")

                if(len(userImg.filename) > 200 ):
                    flash("This image name is way to long!")
                
                else:
                    #Ifall ingen ny profil bild har lagts till vid inputfile så skippar vi uppdatering av filen
                    if(userImg.filename == ''):
                        query = "UPDATE users SET firstname = '%s', surname = '%s', email = '%s' WHERE userID ='%s'" %(fname,lname,email,session['user'])
                    else:
                        query = "UPDATE users SET firstname = '%s', surname = '%s', email = '%s', user_img = '%s' WHERE userID ='%s'" %(fname,lname,email,userImg.filename,session['user'])
                        print("Vi kör detta alltså")
                        userImg.save(os.path.join(app.config["USER_IMAGE_UPLOADS"], userImg.filename))
                    cur.execute(query)
                    conn.commit()
                    session['name'] = fname
                    session['surname'] = lname
            except:
                print("Error!!")

        elif(request.form.get("addMoneyBtn")):
            try:
                amount = int(request.form["makeMoney"])
                if(amount > 0):
                    addMoney(amount,session["user"])
                else:
                    amount = -amount
                    removeMoney(amount,session["user"])
            except:
                flash("That is an invalid amount of money")
                
            
        elif(request.form.get("submitPass")):
            request.form['Password']
            oldPass = request.form['Password']
            newPass = request.form['newPassword']
            newPassAgain = request.form['newPasswordAgain']
            query = "SELECT users.password FROM users WHERE userID='%s'" %(session['user'])
            cur.execute(query)
            conn.commit()
            currentPass = cur.fetchone()[0]

            if(currentPass == oldPass):
                if(newPass == newPassAgain):
                    query = "UPDATE users SET password = '%s' WHERE userID ='%s'" %(newPass,session['user'])
                    cur.execute(query)
                    conn.commit()
                    flash("The password was successfully changed!")
                else:
                    flash("The password doesn't match!")
            else:
                flash("You entered the wrong password!")

    query = "Select users.firstname, users.surname, users.email, users.money, users.user_img from users where userID='%i'" %(session['user'])
    cur.execute(query)
    conn.commit()
    userinfo = cur.fetchone()
    cur.close()
    print(userinfo)
    return render_template('profile.html', userInfo = userinfo)


# Shows all the user´s orders.
@app.route('/profile/orders', methods = ['GET', 'POST'])
def profileOrders():
    cur = conn.cursor()
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))

    if(request.method == 'POST'):
        ordNr = int(request.form['remove_order'])
        removeOrder(user, ordNr)

    # Retrive all order numbers the user have. 
    query = "SELECT order_number FROM orders WHERE userID='%i' AND order_placed=1;" %(user)
    cur.execute(query)
    conn.commit()
    orderNr = cur.fetchall()
    orders = []

    # Retrive all the information from all the orders.
    for orderNum in orderNr:
        # +----------------+---------------+---------+--------+--------------+------------+-------------+
        # | article_number | article_name  | price   | amount | order_number | item total | order total |
        # +----------------+---------------+---------+--------+--------------+------------+-------------+
        query = ''' SELECT articles.article_number,
                        articles.article_name,
                        booked_items.price,
                        booked_items.amount,
                        booked_items.order_number,
                        (booked_items.price * booked_items.amount) AS 'item total',
                        (SELECT SUM(booked_items.price * booked_items.amount)
                            FROM articles, booked_items
                            WHERE articles.article_number=booked_items.article_number AND order_number='%i') AS 'order total'
                    FROM booked_items
                    INNER JOIN articles ON booked_items.article_number=articles.article_number
                    WHERE booked_items.order_number='%i';''' %(orderNum[0], orderNum[0])
        
        cur.execute(query)
        conn.commit()
        order = cur.fetchall()
        orders.append(order) 

    cur.close()
    return render_template('profileOrders.html', orders = orders)


@app.route('/allOrders', methods = ['GET','POST'])
def allOrders():
    cur = conn.cursor()
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))

    if(request.method == 'POST'):
        ordNr = int(request.form['remove_order'])
        cur.execute("SELECT userID FROM orders WHERE order_number=%s",(ordNr,))
        conn.commit()
        us = cur.fetchone()[0]
        removeOrder(us,ordNr)

    # Retrive all order numbers the user have. 
    query = "SELECT order_number FROM orders WHERE order_placed=1;"
    cur.execute(query)
    conn.commit()
    orderNr = cur.fetchall()
    orders = []

    # Retrive all the information from all the orders.
    for orderNum in orderNr:
        # +----------------+---------------+---------+--------+--------------+------------+-------------+
        # | article_number | article_name  | price   | amount | order_number | item total | order total |
        # +----------------+---------------+---------+--------+--------------+------------+-------------+
        query = ''' SELECT articles.article_number,
                        articles.article_name,
                        booked_items.price,
                        booked_items.amount,
                        booked_items.order_number,
                        (booked_items.price * booked_items.amount) AS 'item total',
                        (SELECT SUM(booked_items.price * booked_items.amount)
                            FROM articles, booked_items
                            WHERE articles.article_number=booked_items.article_number AND order_number='%i') AS 'order total',
                        (SELECT userID FROM orders WHERE order_number='%i') AS userID
                    FROM booked_items
                    INNER JOIN articles ON booked_items.article_number=articles.article_number
                    WHERE booked_items.order_number='%i';''' %(orderNum[0], orderNum[0], orderNum[0])
        
        cur.execute(query)
        conn.commit()
        order = cur.fetchall()
        orders.append(order) 

    cur.close()
    return render_template('allOrders.html', orders = orders)



@app.route('/addArticle', methods = ['GET','POST'])
def addArticles():
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))
    
    cur = conn.cursor()

    if(request.method == 'POST'):
        if(request.form.get("submitAdd")):
            try:
                product = request.form.get('article')
                amount = request.form['addAmount']
                increaseArticle(product,int(amount))
                flash("Successfully added " + amount + " product(s)", "success")
            except:
                flash("Not valid input, must be a number!", "error")
        elif(request.form.get("submitRemove")):
            try:
                product = request.form.get('article')
                amount = request.form['removeAmount']
                decreaseArticle(product,int(amount))
                flash("Successfully removed " + amount + " product(s)", "success")
            except:
                flash("Not valid input, must be a number!", "error")
        elif(request.form.get("submitPrice")):
            try:
                product = request.form.get('article')
                newPrice = request.form['changePrice']
                query = "UPDATE articles SET price='%i' WHERE article_number='%i'" %(int(newPrice), int(product))
                cur.execute(query)
                conn.commit()
                flash("Successfully changed the price to " + newPrice + " :-", "success")
            except:
                flash("Not valid input, must be a number!", "error")
        else:
            try:
                articleName = request.form['articleName']
                articlePrice = request.form['articlePrice']
                aricleStock = request.form['articleStock']
                articeInfo = request.form['articleInfo']
                image = request.files['inputFile']

                query = "INSERT INTO articles values (NULL, '%s', '%s', '%s', '%s', '%s')" %(articleName,articlePrice,aricleStock,articeInfo,image.filename)
                cur.execute(query)
                conn.commit()
                #sparar filen till den konfiguerade pathwayen på servern, samt väljer namnet på filen.
                image.save(os.path.join(app.config["ARTICLE_IMAGE_UPLOADS"], image.filename))
                print("image saved")
            except:
                flash("Not valid input!", "error")
    
    query = "Select * from articles"
    cur.execute(query)
    conn.commit()
    articles = cur.fetchall()

    cur.close()
    
    return render_template('addArticle.html', articles = articles)   


@app.route('/overview', methods = ['GET', 'POST'])
def overview():
    if "user" in session:
        user = session["user"]
    else:
        return redirect(url_for("login"))
    cur = conn.cursor()
    query = "Select * from users where role='user';"
    cur.execute(query)
    conn.commit()
    users = cur.fetchall()
    return render_template('overview.html', users = users)


    #--------------------Functions------------------#



    # Om man vill minska antal av en vara updaterar man amount av varan.
def lower_amount(id, user):
    cur = conn.cursor()
    query = "SELECT amount FROM booked_items where article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(id,user)
    cur.execute(query)
    conn.commit()
    amount = cur.fetchone()
    if (amount == None):
        return

    amount = amount[0]
    # Varan kan inte bli mindre än 0
    if amount > 0:
        amount = amount - 1
        query = "UPDATE booked_items SET amount='%i' WHERE article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(amount,id,user)
        cur.execute(query)
        conn.commit()
    if amount == 0:
        remove_from_order(id,user)
    
    cur.close()
    return 


def confirmOrder(): #bekräfta ordern #made by Johan

    cur = conn.cursor()
    user = session["user"]


    #check so that there are enough items in stock
    cur.execute("SELECT booked_items.article_number, booked_items.amount, articles.amount FROM booked_items,articles WHERE order_number = (SELECT order_number FROM orders WHERE userID=%s AND order_placed = 0) AND booked_items.article_number = articles.article_number",user)
    conn.commit()
    articles = cur.fetchall()
    if(len(articles) == 0):
        return "Empty"
    for article in articles:
        if(article[1] > article[2]):
            return False            #if there are not enough items in stock, return False


    #lower the amount on those rows
    for article in articles:
        cur.execute("UPDATE articles SET articles.amount = articles.amount - %s WHERE articles.article_number=%s",(article[1], article[0],))
        conn.commit()

    #make order_placed = 1
    cur.execute("UPDATE orders SET order_placed = 1 WHERE userID = %s AND order_placed = 0",user)
    conn.commit()


    cur.close()
    return True


def removeOrder(user, ordNum): #ta bort en befintlig order #made by Johan
    cur = conn.cursor()
    cur.execute("SELECT sum(booked_items.price * booked_items.amount) FROM booked_items WHERE order_number=%s",(ordNum,))
    conn.commit()
    amount = cur.fetchone()[0]
    if(transaction(24,user,amount)):

        #hitta artiklarna och antalet av dem och öka antalet på hyllan
        cur.execute("SELECT booked_items.article_number, booked_items.amount FROM booked_items WHERE order_number = %s",(ordNum,))
        conn.commit()
        articles = cur.fetchall()
        for article in articles:
            artID = article[0]
            artAmount = article[1]
            cur.execute("UPDATE articles SET articles.amount = articles.amount + %s WHERE articles.article_number = %s",(artAmount, artID,))
            conn.commit()

        cur.execute("DELETE FROM orders WHERE userID = %s AND order_number = %i"%(user, ordNum))
        conn.commit()
    
    cur.close()
    return

# Om man trycker på ta bort så tas varan bort från varukorgen.
def remove_from_order(artID,user):
    cur = conn.cursor()
    query = "DELETE FROM booked_items WHERE article_number='%i' AND order_number=(SELECT order_number FROM orders WHERE userID='%s' AND order_placed=0);" %(artID,user)
    cur.execute(query)
    conn.commit()
    cur.close()
    return 

def add_to_cart(articleNum, user):
    cur = conn.cursor()
    # Kolla om det finns en aktiv varukorg till användaren.
    query = "SELECT * FROM orders WHERE userID='%s' AND order_placed=0;" %(user)
    cur.execute(query)
    conn.commit()
    response = cur.fetchone()
    if (response == None):
        timeStamp = datetime.now()
        timeStampDay = timeStamp.day
        timeStampMonth = timeStamp.month

        # Check if month or day is single digit. If soo, add a zero.
        if(timeStampDay < 10):
            timeStampDay = "0" + str(timeStamp.day)
        if(timeStampMonth < 10):
            timeStampMonth = "0" + str(timeStamp.month)
        
        # Set up timeStap fro when the order i created.
        timeStamp = str(timeStamp.year) + timeStampMonth + timeStampDay
        
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
        query = "INSERT INTO booked_items VALUES('%s', '%s', 1, 0);" %(orderNum, articleNum)
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
    

def addGrade(artID, userID, grade): #made by Johan
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



# Add a comment to an article.
def addComment(articleID, userID, comment):
    cur = conn.cursor()

    query = "SELECT * FROM opinion WHERE article_number='%i' AND userID='%i';" %(articleID, userID)
    cur.execute(query)
    conn.commit()

    # Check if user have already made a comment on this article.
    # If no, create a new comment.
    try:
        if cur.fetchone() == None:
            query = "INSERT INTO opinion VALUES('%i', '%i', NULL, '%s');" %(articleID, userID, comment)
            cur.execute(query)
            conn.commit()
        # If yes, update the comment.
        else:
            query = "UPDATE opinion SET comment='%s' WHERE article_number='%i' AND userID='%i';" %(comment, articleID, userID)
            cur.execute(query)
            conn.commit()
    except:
        flash("Comment could not be placed, make sure it's no longer than 200 characters", "error")
    return #redirect(url_for("index"))#här ska den redirecta tillbaka till artikelsidan.

def transaction(looser, gainer,amount): #made by Johan
    #gainer = 24, this is the userID for the bank
    cur = conn.cursor()
    try:
        query = "START TRANSACTION"
        cur.execute(query)

        query = "UPDATE users SET money = money - %s WHERE userID = %s"%(amount, looser)#someone looses money
        cur.execute(query)

        query = "UPDATE users SET money = money + %s WHERE userID = %s"%(amount, gainer)#someone gains money
        cur.execute(query)

        query = "COMMIT"
        cur.execute(query)

        conn.commit()
        cur.close()
        return True
    except:
        
        conn.rollback()
        cur.close()
        return False

def sufficientFunds(amount, user): #checks if there is enough money in the account to purchase #made by Johan
    cur = conn.cursor()
    query = "SELECT money FROM users WHERE userID = %s"%(user)
    cur.execute(query)
    conn.commit()
    currAmount = cur.fetchone()
    #if the users lacks sufficient funds
    if(amount > currAmount[0]):
        flash("You don't have enough money to buy these products!")
        return False
    cur.close()
    return True

    

def addMoney(amount, user): #made by Johan
    cur = conn.cursor()
    #Made by Robin 
    query = "SELECT money FROM users WHERE userID = %s"%(user)
    cur.execute(query)
    conn.commit()
    currAmount = cur.fetchone()
    #if the users lacks sufficient funds
    val = int(currAmount[0] + amount)
    if(abs(val) <= 0x0FFFFFFF):
        query = "UPDATE users SET money = money + %i WHERE userID = %s"%(amount, user)
        cur.execute(query)
        conn.commit()
    else:
        flash("The amount you tried to add is to large for a 32 bit signed interger, try something smaller")
    cur.close()
    return


def removeMoney(amount, user): #made by Johan
    cur = conn.cursor()
    query = "SELECT money FROM users WHERE userID = %s"%(user)
    cur.execute(query)
    conn.commit()
    currAmount = cur.fetchone()
    #if the users lacks sufficient funds
    if(amount > currAmount[0]):
        flash("You can remove money you don't have...")
        return
    query = "UPDATE users SET money = money - %i WHERE userID = %s"%(amount, user)
    cur.execute(query)
    conn.commit()
    cur.close()
    return
    
def decreaseArticle(artID, amount): #made by Johan 
    if(amount < 0):
        return

    cur = conn.cursor()
    query = "UPDATE articles SET amount = amount - %s WHERE article_number=%s"%(amount, artID)
    cur.execute(query)
    conn.commit()

    cur.close()
    return


def increaseArticle(artID, amount): #made by Johan
    if(amount < 0):
        return

    cur = conn.cursor()
    query = "UPDATE articles SET amount = amount + %s WHERE article_number=%s"%(amount, artID)
    cur.execute(query)
    conn.commit()

    cur.close()
    return


if __name__ == '__main__':
    createTables()
    app.debug = True
    app.run(host = '0.0.0.0')
