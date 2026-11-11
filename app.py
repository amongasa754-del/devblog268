import os, sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'devblog268.db')
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-before-deploying')
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'change-me-now')

SERVERS = [
    {'name': 'DEVBlog 268 | MAIN', 'mode': 'Основной сервер', 'rate': 'x2', 'team': 'MAX 4', 'wipe': 'Информация скоро появится', 'address': 'IP:PORT — добавь адрес сервера'},
    {'name': 'DEVBlog 268 | CLASSIC', 'mode': 'Классический сервер', 'rate': 'x1', 'team': 'Без ограничений', 'wipe': 'Информация скоро появится', 'address': 'IP:PORT — добавь адрес сервера'},
    {'name': 'DEVBlog 268 | TRAINING', 'mode': 'Тренировочный сервер', 'rate': '—', 'team': 'Тренировка', 'wipe': 'Без вайпа', 'address': 'IP:PORT — добавь адрес сервера'},
]

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Обновление',
            body TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )''')
        count = con.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        if count == 0:
            con.execute('INSERT INTO posts (title, category, body) VALUES (?, ?, ?)', (
                'Добро пожаловать в DEVBlog 268', 'НОВОСТИ',
                'Это стартовая новость проекта. Здесь будут публиковаться обновления, изменения игровых механик и объявления о вайпах.'))
            con.execute('INSERT INTO posts (title, category, body) VALUES (?, ?, ?)', (
                'Разработка проекта началась', 'РАЗРАБОТКА',
                'Мы готовим сайт, серверную инфраструктуру и сообщество. Следите за новостями — подробности появятся здесь.'))

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login', next=request.path))
        return fn(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    with db() as con:
        posts = con.execute('SELECT * FROM posts ORDER BY id DESC LIMIT 6').fetchall()
    return render_template('index.html', posts=posts, servers=SERVERS)

@app.route('/news')
def news():
    with db() as con:
        posts = con.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    return render_template('news.html', posts=posts)

@app.route('/servers')
def servers():
    return render_template('servers.html', servers=SERVERS)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(request.args.get('next') or url_for('admin'))
        flash('Неверный логин или пароль', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin():
    with db() as con:
        posts = con.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    return render_template('admin.html', posts=posts)

@app.route('/admin/create', methods=['POST'])
@admin_required
def create_post():
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'Обновление').strip()
    body = request.form.get('body', '').strip()
    if not title or not body:
        flash('Заполни заголовок и текст новости', 'error')
        return redirect(url_for('admin'))
    with db() as con:
        con.execute('INSERT INTO posts (title, category, body) VALUES (?, ?, ?)', (title, category, body))
    flash('Новость опубликована', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:post_id>', methods=['POST'])
@admin_required
def delete_post(post_id):
    with db() as con:
        con.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    flash('Новость удалена', 'success')
    return redirect(url_for('admin'))

@app.route('/health')
def health():
    return {'status': 'ok', 'project': 'DEVBlog 268'}

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
