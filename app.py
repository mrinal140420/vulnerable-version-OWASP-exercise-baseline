# vulnerable_app.py
import os
from flask import (
    Flask, render_template, request, redirect, url_for, abort,
    send_from_directory, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user, login_required,
    current_user, UserMixin
)
from werkzeug.utils import secure_filename
from sqlalchemy import text  # <-- needed for raw SQL execution in SQLAlchemy 2.x

# --- config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# serve uploads from static (insecure, intentionally)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'insecure-secret-for-lab-only',
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(BASE_DIR, 'app.db'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'UPLOAD_FOLDER': UPLOAD_FOLDER,
})

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # intentionally store plaintext password (INSECURE for practice)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- routes (intentionally vulnerable / minimal checks) ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', user=current_user)
    return render_template('index.html', user=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # minimal, intentionally insecure (plaintext password compare)
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        # generic invalid response
        return 'Invalid', 401
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# IDOR / Broken Access Control: no server-side owner check beyond login in original.
# This keeps the vulnerability: direct raw SQL with concatenated uid -> SQL injection risk.
@app.route('/profile/<int:uid>')
@login_required
def profile(uid):
    # VULNERABLE: direct string-format SQL (intended for practice)
    raw = "SELECT id, username, password, is_admin FROM user WHERE id = %s" % uid

    # SQLAlchemy 2.x compatibility: use session.execute(text(...))
    # Note: this preserves the raw-string vulnerability (SQL injection) intentionally for the lab.
    res = db.session.execute(text(raw)).fetchall()

    if not res:
        abort(404)
    row = res[0]
    # returns plaintext password as in your original vulnerable example
    user_obj = {'id': row[0], 'username': row[1], 'password': row[2], 'is_admin': bool(row[3])}
    return render_template('profile.html', user=user_obj)


# Admin panel (protected only by is_admin flag shown in UI but not enforced)
# Intentionally left open (vulnerable) as in original example
@app.route('/admin')
def admin():
    users = User.query.all()
    return render_template('admin.html', users=users)


# File upload (insecure)
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return 'No file', 400
        # VULNERABLE: no extension check, saving original filename (can overwrite, path issues)
        filename = secure_filename(f.filename)
        if filename == '':
            return 'Bad filename', 400
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(path)
        return 'Uploaded: ' + filename
    return render_template('upload.html')


# serve uploads (unsafe: served from web root)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # intentionally no access control
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# initialize DB command
@app.cli.command('initdb')
def initdb():
    db.drop_all()
    db.create_all()
    # create demo users with plaintext passwords (INSECURE but matches original)
    admin = User(username='admin', password='admin', is_admin=True)
    alice = User(username='alice', password='alice', is_admin=False)
    bob = User(username='bob', password='bob', is_admin=False)
    db.session.add_all([admin, alice, bob])
    db.session.commit()
    print('DB initialized')

if __name__ == '__main__':
    # DEV convenience: create DB tables and seed demo users if missing.
    # WARNING: This seeds plaintext demo passwords and is insecure — only for isolated lab use.
    with app.app_context():
        db.create_all()
        # seed demo users only if table is empty
        try:
            cnt = User.query.count()
        except Exception:
            cnt = 0
        if cnt == 0:
            admin = User(username='admin', password='admin', is_admin=True)
            alice = User(username='alice', password='alice', is_admin=False)
            bob = User(username='bob', password='bob', is_admin=False)
            db.session.add_all([admin, alice, bob])
            db.session.commit()
            print('DB created and seeded demo users (admin/alice/bob)')
        else:
            print(f'DB already initialized (user count = {cnt})')
    # run Flask dev server (insecure mode for lab)
    app.run(debug=True)
