# app.py (hardened)
import os
import uuid
from flask import (
    Flask, render_template, request, redirect, url_for, abort,
    send_from_directory, flash, current_app
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user, login_required,
    current_user, UserMixin
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from flask_wtf import CSRFProtect
from flask_talisman import Talisman

# --- config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'change-this-secret-in-prod'),
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(BASE_DIR, 'app.db'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'UPLOAD_FOLDER': UPLOAD_FOLDER,
    # Cookie settings (set Secure=True in production with HTTPS)
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    # 'SESSION_COOKIE_SECURE': True,  # enable in prod when using HTTPS
})

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)

# Talisman for secure headers and CSP
csp = {
    'default-src': ["'self'"],
    # allow styles/scripts from self only; extend if you add CDNs
}
Talisman(app,
        content_security_policy=csp,
        frame_options='DENY',
        strict_transport_security=True,
        strict_transport_security_preload=True,
        force_https=False)  # set True in prod with TLS

# --- models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # hashed
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper: allowed upload extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_safe_url(target):
    # allow only relative URLs or same-host absolute URLs
    from urllib.parse import urlparse
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(target)
    return (redirect_url.scheme in ('', 'http', 'https') and
            (redirect_url.netloc == '' or redirect_url.netloc == host_url.netloc))

# --- routes ---
@app.route('/')
def index():
    return render_template('index.html', user=current_user if current_user.is_authenticated else None)

# Login form uses CSRF token (template updated)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        next_url = request.args.get('next') or url_for('index')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if not is_safe_url(next_url):
                return redirect(url_for('index'))
            return redirect(next_url)
        # generic invalid response
        flash('Invalid username or password', 'danger')
        return render_template('login.html'), 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Profile view: use ORM and enforce access control
@app.route('/profile/<int:uid>')
@login_required
def profile(uid):
    user = User.query.get(uid)
    if not user:
        abort(404)
    # Authorization: allow only owner or admin
    if current_user.id != user.id and not current_user.is_admin:
        abort(403)
    # Don't expose hashed password in template
    safe_user = {'id': user.id, 'username': user.username, 'is_admin': user.is_admin}
    return render_template('profile.html', user=safe_user)

# Admin panel: require login and is_admin
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)
    users = User.query.all()
    return render_template('admin.html', users=users)

# Upload hardening: whitelist, rename, store safely, list only for admin/owner
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            flash('No file provided', 'warning')
            return redirect(url_for('upload'))
        filename = secure_filename(f.filename)
        if filename == '':
            flash('Invalid filename', 'warning')
            return redirect(url_for('upload'))
        if not allowed_file(filename):
            flash('File type not allowed', 'warning')
            return redirect(url_for('upload'))
        ext = filename.rsplit('.', 1)[1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
        f.save(path)
        flash('Uploaded: ' + safe_name, 'success')
        return redirect(url_for('upload'))
    # list uploads only for admin or owner (simple: admin only)
    files = []
    if current_user.is_admin:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('upload.html', files=files)

# serve uploads: require login, only admin or owner can download (here: admin only)
@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    if not current_user.is_admin:
        abort(403)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# init DB (hashed passwords)
@app.cli.command('initdb')
def initdb():
    db.drop_all()
    db.create_all()
    # create demo users with hashed passwords (secure for lab)
    admin = User(username='admin', password=generate_password_hash('admin'), is_admin=True)
    alice = User(username='alice', password=generate_password_hash('alice'), is_admin=False)
    bob = User(username='bob', password=generate_password_hash('bob'), is_admin=False)
    db.session.add_all([admin, alice, bob])
    db.session.commit()
    print('DB initialized with hashed demo users (admin/alice/bob)')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        try:
            cnt = User.query.count()
        except Exception:
            cnt = 0
        if cnt == 0:
            admin = User(username='admin', password=generate_password_hash('admin'), is_admin=True)
            alice = User(username='alice', password=generate_password_hash('alice'), is_admin=False)
            bob = User(username='bob', password=generate_password_hash('bob'), is_admin=False)
            db.session.add_all([admin, alice, bob])
            db.session.commit()
            print('DB created and seeded demo users (admin/alice/bob)')
        else:
            print(f'DB already initialized (user count = {cnt})')
    # DEV: run without debug True in production
    app.run(debug=False)
