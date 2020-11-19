from flask import Flask, render_template, request, redirect,url_for
from flaskext.mysql import MySQL


app = Flask(__name__)

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
        cur = conn.cursor()
        cur.execute("SELECT * FROM article WHERE article_name = %s",text)
        rv = str(cur.fetchall())
        return rv

    return render_template('search.html')


@app.route('/admin', methods = ['GET', 'POST']) #admin page to add items to the database
def admin():
    if(request.method == "POST"):
        cur = conn.cursor()
        query = request.form["configure"]
        cur.execute(query)
        conn.commit()
        cur.close()

    return render_template('admin.html')


@app.route('/login', methods = ['GET', 'POST']) 
def login():
    if(request.method == 'POST'):
        email = request.form["email"]
        pwd = request.form["pwd"]

        #search for the email in the database
        cur = conn.cursor()
        query = "SELECT email FROM users WHERE email='" + email +"'"
        cur.execute(query)
        conn.commit()
        rv = str(cur.fetchone())
        return rv

    return render_template('login.html')

@app.route('/register', methods = ['GET', 'POST']) 
def register():
    if(request.method == 'POST'):
        name = request.form["name"]
        surname = request.form["surname"]
        email = request.form["Email_input"]
        password = request.form["Pass_input"]
        password2 = request.form["Pass_input2"]
        
        
        if(password == password2):  
            cur = conn.cursor()
            query = "INSERT INTO users VALUES (NULL,'" + name + "' ,'" + surname + "', '" + email + "','" + password + "','user');"
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

if __name__ == '__main__':
    createTables()
    app.debug = True
    app.run(host = '0.0.0.0')