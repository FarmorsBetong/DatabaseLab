from flask import Flask
from flaskext.mysql import MySQL
app = Flask(__name__)

mysql = MySQL()
mysql.init_app(app)

app.config['MYSQL_DATABASE_PASSWORD'] = 'robin123'
app.config['MYSQL_DATABASE_DB'] = 'test'
app.config['MYSQL_DATABASE_USER'] = 'root'

cur = mysql.connect().cursor()

# Create tables
cur.execute('''CREATE TABLE IF NOT EXISTS users(
    userID INT UNSIGNED AUTO_INCREMENT NOT NULL,
    name VARCHAR(100) NOT NULL,
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
        
cur.execute('''CREATE TABLE IF NOT EXISTS conveyor_belt(
    order_number INT UNSIGNED NOT NULL,
    article_number INT UNSIGNED NOT NULL,
    FOREIGN KEY(order_number) REFERENCES orders(order_number),
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
    

@app.route('/')
def index():
	return "hello world, and everyone, testing"


if __name__ == '__main__':
	#app.debug = True
	app.run(host = '0.0.0.0')


def test():

	return "test"