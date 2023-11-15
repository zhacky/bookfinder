from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash 
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_uploads import configure_uploads, UploadSet, DOCUMENTS

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret_key_1234'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:12345678@0.0.0.0:5432/finder'
app.config['SQLALCHEMEY_TRACK_MODIFICATIONS'] = False
app.config['UPLOADED_PDFS_DEST'] = 'uploads/pdfs'
db = SQLAlchemy(app)
pdfs = UploadSet('pdfs', DOCUMENTS)

configure_uploads(app, pdfs)


# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    pdf = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=True)

class BookForm(FlaskForm):
    title = db.Column(db.String(), nullable=False)
    pdf = FileField('Upload PDF', validators=[FileAllowed(['pdf'], 'PDFs only!')])
# create database table using `flask shell` in the terminal
# db.create_all()

@app.route("/")
def index():
    if session.get('logged_in'):

        books = Book.query.all()    
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        
    return render_template('index.html', email=user_email if user_email else None)

@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')


        user = User.query.filter_by(email=email).first()

    

        if user and user.check_password(password):
            session['logged_in'] = True
            session['user_id'] = user.id
            session['user_email'] = user.email 

            return redirect(url_for('dashboard'))
        else: 
            error = 'Invalid email or password.  Please try again.'

    return render_template('login.html', error=error if 'error' in locals() else None)

@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for('index'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            error = 'Email address already registered'

        else:
            new_user = User(email=email)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))
    
    return render_template('register.html', error=error if 'error' in locals() else None)

# -------------------------------------------- #
# --------------- dashboard ------------------ #
# -------------------------------------------- #
@app.route("/dashboard")
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    books = Book.query.all()
    
    user_id = session.get('user_id')
    user_email = session.get('user_email')

    return render_template("dashboard.html", 
                           user_id=user_id, 
                           user_email = user_email,
                           books=books if books else None)



# -------------------------------------------- #
# --------------- books ---------------------- #
# -------------------------------------------- #
@app.route('/book/<int:book_id>')
def view_book(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('view_book.html', book=book)

@app.route('/create_book', methods=['GET', 'POST'])
def create_book():
    form = BookForm()
    
    if form.validate_on_submit():
        title = form.title.data
        pdf = form.pdf.data
        
        pdf_filename = pdfs.save(pdf)
        
        new_book = Book(title=title, pdf=pdf_filename)
        db.session.add(new_book)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    return render_template('create_book.html', form=form)

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)
    
    if form.validate_on_submit():
        form.populate_obj(book)
        
        if form.pdf.data:
            pdf_filename = pdfs.save(form.pdf.data)
            book.pdf = pdf_filename
            
        db.session.commit()
        
        return redirect(url_for('index'))
    
    return render_template('edit_book.html', form=form, book=book)

@app.route('/delete_book/<int:book_id>', methods=['GET', 'POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        pdfs.delete(book.pdf)
        db.session.delete(book)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    return render_template('delete_book.html', book=book)



if __name__ == '__main__':
    app.run(debug=True)