from flask import Flask, render_template, request, redirect, url_for,session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app=Flask(__name__)
app.secret_key='key'

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=' '
app.config['MYSQL_DB']=' '

mysql=MySQL(app)

def create_signup_table():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signup (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            phone varchar(12)       
        )
    ''')
    mysql.connection.commit()
    cursor.close()

@app.route('/')
@app.route('/login',methods=['GET','POST'])
def login() :
    msg=''
    if request.method=='POST' and 'email' in request.form and 'password' in request.form:
        email=request.form['email']
        password=request.form['password']

        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM signup WHERE email=%s and password=%s',(email,password,))
        signup=cursor.fetchone()
        if signup :
            session['loggedin']=True
            session['id']=signup['id']
            session['email']=signup['email']
            session['name']=signup['name']
            msg= 'welcome'+session['name']
            return redirect(url_for('index'))
        else :
            msg='incorrect email or password'
    return render_template('login.html',msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin',None)
    session.pop('id',None)
    session.pop('email',None)
    return redirect (url_for('login'))

@app.route('/signup',methods=['GET','POST'])
def signup():
    msg=''
    if request.method=='POST' and 'email'in request.form and 'password' in request.form  and 'storename' in request.form:
        email=request.form ['email']
        password=request.form['password']
        name=request.form['name']
        phone=request.form['phone']
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM signup WHERE email=%s',(email,))
        signup=cursor.fetchone()
        if signup : 
            msg='account already exists'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg='invalid email'
        elif not re.match(r'[A-Za-z]+', name):
            msg='Name must contain only words'
        else :
            cursor.execute('INSERT INTO signup VALUES(NULL,%s,%s,%s,%s,)',(email,password,name,phone,))
            mysql.connection.commit()
            msg='you have logged in ',name
    elif request.method=='POST':
        msg='please fill'
    return redirect(url_for('login'))
