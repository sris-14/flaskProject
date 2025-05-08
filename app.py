from flask import Flask, jsonify, make_response, request, render_template, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import uuid
import jwt
import datetime


app = Flask(__name__)

# Secret key for session management
app.config['SECRET_KEY'] = '52df3278d59bc15020abf757fefd72fd'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db' 

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db-init
db = SQLAlchemy(app)

@app.route('/')
def home():
    return render_template('home.html')


# function to check for valid user token
def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = session.get('jwt_token', None)
        if not token:
            flash("Please login to access this page", "danger")
            return redirect(url_for('login_user'))

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = Users.query.filter_by(public_id=data['public_id']).first()
        except Exception as e:
            flash("Session expired or invalid. Please login again!", "danger")
            return redirect(url_for('login_user'))
        return f(current_user, *args, **kwargs)
    return decorator


# User table 
class Users(db.Model):
   id = db.Column(db.Integer, primary_key = True)
   public_id = db.Column(db.String(50), unique = True)
   name = db.Column(db.String(50))
   password = db.Column(db.String(128))
   admin = db.Column(db.Boolean)
   
# Book table
class Books(db.Model):
   id = db.Column(db.Integer, primary_key = True)
   user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
   name = db.Column(db.String(50), unique = True, nullable = False)
   author = db.Column(db.String(50), nullable = False)
   publisher = db.Column(db.String(50), nullable = False)
   book_prize = db.Column(db.Integer)

# Issue/Return table
class Issues(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    issue_date = db.Column(db.DateTime, default = datetime.datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable = True)   

with app.app_context():
    db.create_all() 

@app.route('/library')
def library_dashboard():
    return render_template('library.html')     

# route for signing up 
@app.route('/register', methods=['GET', 'POST'])
def signup_user():
    if request.method == 'POST':
        # get a form data 
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_pwd = generate_password_hash(password)

        new_user = Users(public_id=str(uuid.uuid4()), name=name, password=hashed_pwd, admin=False)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'success')
        return redirect(url_for('library_dashboard'))
    else:
        return render_template('register.html')


# route for loggin in
@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = Users.query.filter_by(name=name).first()
        if user and check_password_hash(user.password, password):
            token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'], "HS256")
            session['jwt_token'] = token
            flash('Login successful!', 'success')
            return redirect(url_for('library_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')



# route for registered users
@app.route('/users', methods=['GET'])
def get_all_users(): 
 
   users = Users.query.all()
   result = []  
   for user in users:  
       user_data = {}  
       user_data['public_id'] = user.public_id 
       user_data['name'] = user.name
       user_data['password'] = user.password
       user_data['email'] = user.email
       user_data['admin'] = user.admin
     
       result.append(user_data)  
   return jsonify({'users': result})

# route for books
@app.route('/add_book', methods=['GET', 'POST'])
@token_required
def add_book(current_user):
    if request.method == 'POST':
        name = request.form['name']
        author = request.form['author']
        publisher = request.form['publisher']
        book_price = request.form['book_price']
        new_book = Books(name=name, author=author, publisher=publisher, book_price=book_price, user_id=current_user.id)
        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('get_books'))
    return render_template('add_book.html')


# route to allow users to get all books
@app.route('/books', methods=['GET'])
@token_required
def get_books(current_user):
    books = Books.query.filter_by(user_id=current_user.id).all()
    return render_template('books.html', books=books)


# route to issue a book
@app.route('/issue_book', methods=['GET','POST'])
@token_required
def issue_book(current_user):
    if request.method == 'POST':
        book_id = request.form['book_id']
        book = Books.query.filter_by(id=book_id).first()
        if not book:
            flash('Book not found', 'danger')
        else:
            new_issue = Issues(book_id=book.id, user_id=current_user.id, issue_date=datetime.datetime.utcnow())
            db.session.add(new_issue)
            db.session.commit()
            flash('Book issued successfully!', 'success')
        return redirect(url_for('get_books'))

    books = Books.query.all()
    return render_template('issue_book.html', books=books)


# route to get all issue/return records
@app.route('/return/<int:issue_id>', methods=['POST'])
@token_required
def return_book(current_user, issue_id):
    issue = Issues.query.filter_by(id=issue_id, user_id=current_user.id).first()
    if not issue:
        flash('Issue record not found!', 'danger')
        return redirect(url_for('get_issues'))
    if issue.return_date:
        flash('Book is already returned', 'warning')
    else:
        issue.return_date = datetime.datetime.utcnow()
        db.session.commit()
        flash('Book returned successfully!', 'success')
    return redirect(url_for('get_issues'))


# route to delete books
@app.route('/books/<book_id>', methods=['DELETE'])
@token_required
def delete_book(current_user, book_id): 
 
   book = Books.query.filter_by(id=book_id, user_id=current_user.id).first()  
   if not book:  
       return jsonify({'message': 'book does not exist'})  
 
   db.session.delete(book) 
   db.session.commit()  
   return jsonify({'message': 'Book deleted'})

# logout route
@app.route('/logout')
def logout():
    session.pop('jwt_token', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

 
if  __name__ == '__main__': 
    app.run(debug=True)
