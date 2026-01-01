import redis
import datetime
import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from functools import wraps
from dotenv import load_dotnenv

load_dotenv()

ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "default_di_emergenza")
STUDENT_PASS = os.getenv("STUDENT_PASSWORD", "default_di_emergenza")

app = Flask(__name__)
app.secret_key = os.getenv "FLASK_SECRET_KEY"
db = redis.Redis(host='database', port=6379, decode_responses=True)

RESOURCES = {
    "Conversazione": "https://link-conversazione.com",
    "Esercizi": "https://link-esercizi.com",
    "Grammatica": "https://link-grammatica.com",
    "Libri": "https://link-libri.com",
    "Video": "https:https://www.youtube.com/@lucreziaoddone"
    "Scrittura": "https://link-scrittura.com",
    "Giochi": "https://link-giochi.com"
}

STYLE = """
<style>
    :root { --bg: #f8fafc; --panel: #ffffff; --accent: #0284c7; --danger: #e11d48; --warning: #f59e0b; --text-main: #1e293b; --text-dim: #64748b; --border: #e2e8f0; }
    body { font-family: 'Inter', sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; }
    .header { background: white; padding: 0.75rem 2rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .main-layout { display: grid; grid-template-columns: 240px 1fr; gap: 2rem; max-width: 1200px; margin: 0 auto; padding: 2rem; }
    .side-card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; position: sticky; top: 5rem; }
    .side-link { display: block; padding: 0.6rem 0.8rem; color: var(--text-dim); text-decoration: none; border-radius: 8px; font-size: 0.9rem; transition: 0.2s; }
    .side-link:hover { background: #f1f5f9; color: var(--accent); }
    .card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); position: relative; }
    .btn { padding: 0.6rem 1.2rem; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.85rem; border: none; display: inline-flex; align-items: center; gap: 6px; transition: 0.2s; text-decoration: none; }
    .btn-primary { background: var(--accent); color: white; }
    .btn-danger { background: var(--danger); color: white; }
    .btn-warning { background: var(--warning); color: white; }
    .btn-outline { background: white; border: 1px solid var(--border); color: var(--text-dim); }
    .btn-outline:hover { border-color: var(--accent); color: var(--accent); }
    input, textarea { background: #fdfdfd; border: 1px solid var(--border); padding: 0.75rem; border-radius: 8px; width: 100%; margin-bottom: 0.75rem; box-sizing: border-box; }
    .reaction-bar { display: flex; gap: 10px; margin-top: 15px; border-top: 1px solid #f1f5f9; padding-top: 10px; }
    .badge-doubt { font-size: 0.75rem; background: #fff7ed; color: #c2410c; padding: 4px 10px; border-radius: 6px; border: 1px solid #ffedd5; margin-top: 5px; display: inline-block; }
</style>
"""

BOARD_HTML = """
<!DOCTYPE html><html><head>{{ style|safe }}</head><body>
<div class="header">
    <div style="display:flex; align-items:center; gap:20px;">
        <h2 style="margin:0; color:var(--accent);">🎓 Aula 2026</h2>
        {% if live_link %}<a href="{{ live_link }}" target="_blank" class="btn btn-danger">🔴 LIVE</a>{% endif %}
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <span>{{ session['username'] }}</span>
        <a href="/logout" class="btn btn-outline">Esci</a>
    </div>
</div>

<div class="main-layout">
    <aside class="sidebar"><div class="side-card">
        <small style="font-weight:700; color:var(--text-dim);">RISORSE</small>
        <nav style="margin-top:10px;">
            {% for label, url in res.items() %}<a href="{{ url }}" target="_blank" class="side-link">🔗 {{ label }}</a>{% endfor %}
        </nav>
    </div></aside>

    <main class="content-area">
        {% if session.get('is_admin') %}
        <div class="card" style="border-left: 5px solid #eab308;">
            <h4 style="margin:0;">Docente: Controllo Totale</h4>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:10px;">
                <div style="background:#f8fafc; padding:10px; border-radius:8px; border:1px solid var(--border); height:110px; overflow-y:auto;">
                    {% for s in registro %}<div style="font-size:0.8rem; display:flex; justify-content:space-between;">{{ s.nome }} <span>{{ s.stato }}</span></div>{% endfor %}
                </div>
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <form action="/set_live" method="POST" style="display:flex; gap:5px;"><input name="live_url" placeholder="Link Live" style="margin:0;"><button class="btn btn-primary">Avvia</button></form>
                    <div style="display:flex; gap:5px;"><a href="/stop_live" class="btn btn-danger" style="flex:1;">⏹️ Stop</a><a href="/wipe/presenze" class="btn btn-outline">Reset Presenze</a></div>
                </div>
            </div>
            <div style="margin-top:10px; display:flex; gap:10px;">
                <form action="/upload_students" method="POST" style="flex:1; display:flex; gap:5px;"><input name="student_list" placeholder="Nomi..." style="margin:0;"><button class="btn btn-outline">Carica</button></form>
                <a href="/wipe/post" class="btn btn-danger" style="background:#991b1b;">Svuota Bacheca</a>
            </div>
        </div>
        {% else %}<div class="card" style="text-align:center; background:#f0f9ff;"><a href="/segna_presenza" class="btn btn-primary">📍 Conferma Presenza</a></div>{% endif %}

        <div class="card"><form action="/add" method="POST"><input name="title" placeholder="Argomento..." required><textarea name="content" rows="2" placeholder="Spiegazione o link..." required></textarea><button class="btn btn-primary">Pubblica</button></form></div>

        {% for entry in entries %}
        <div class="card">
            <small style="color:var(--text-dim);">👤 {{ entry.author }} • {{ entry.date }}</small>
            <h3 style="margin:5px 0;">{{ entry.title }}</h3>
            <p style="white-space:pre-wrap;">{{ entry.text }}</p>
            
            {% if entry.doubters %}
            <div class="badge-doubt">🤔 Dubbi da: {{ entry.doubters|join(', ') }}</div>
            {% endif %}

            <div class="reaction-bar">
                <a href="/react/{{ entry.id }}/capito" class="btn btn-outline" style="font-size:0.75rem;">💡 Capito ({{ entry.capito }})</a>
                <a href="/react/{{ entry.id }}/dubbio" class="btn btn-warning" style="font-size:0.75rem;">❓ Ho un dubbio</a>
            </div>
        </div>
        {% endfor %}
    </main>
</div>
</body></html>
"""

@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('login'))
    raw = db.lrange('competenze', 0, -1)
    live, registro = db.get('aula_live'), []
    if session.get('is_admin'):
        lista, presenze = db.smembers('lista_ufficiale'), db.hgetall('presenze_oggi')
        for nome in sorted(lista): registro.append({'nome': nome, 'stato': '✅' if nome in presenze else '❌'})
    
    entries = []
    for idx, e in enumerate(raw):
        p = e.split('|')
        if len(p) >= 4:
            entries.append({
                'id': idx, 'date': p[0], 'author': p[1], 'title': p[2], 'text': p[3],
                'capito': db.get(f"react:{idx}:capito") or 0,
                'doubters': list(db.smembers(f"react:{idx}:doubters"))
            })
    entries.reverse()
    return render_template_string(BOARD_HTML, style=STYLE, entries=entries, live_link=live, registro=registro, res=RESOURCES)

@app.route('/react/<int:pid>/<type>')
def react(pid, type):
    if type == 'capito': db.incr(f"react:{pid}:capito")
    elif type == 'dubbio': db.sadd(f"react:{pid}:doubters", session['username'])
    return redirect(url_for('index'))

@app.route('/wipe/<tipo>')
def wipe(tipo):
    if session.get('is_admin'):
        if tipo == 'post':
            db.delete('competenze')
            for key in db.scan_iter("react:*"): db.delete(key)
        elif tipo == 'presenze': db.delete('presenze_oggi')
    return redirect(url_for('index'))

# --- LE ALTRE ROTTE RIMANGONO INVARIATE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if (u == 'admin' and p == 'ADMIN_PASS') or (p == 'STUDENT_PASS' and u):
            session['username'], session['is_admin'] = (u, u == 'admin')
            return redirect(url_for('index'))
    return render_template_string("<html><head>{{s|safe}}</head><body style='display:flex; align-items:center; justify-content:center;'><div class='card' style='width:300px;'><form method='POST'><h2>Login</h2><input name='username' placeholder='Nome'><input type='password' name='password' placeholder='Pass'><button class='btn btn-primary' style='width:100%'>Entra</button></form></div></body></html>", s=STYLE)

@app.route('/set_live', methods=['POST'])
def set_live():
    if session.get('is_admin'): db.set('aula_live', request.form.get('live_url'))
    return redirect(url_for('index'))

@app.route('/stop_live')
def stop_live():
    if session.get('is_admin'): db.delete('aula_live')
    return redirect(url_for('index'))

@app.route('/upload_students', methods=['POST'])
def upload_students():
    if session.get('is_admin'):
        db.delete('lista_ufficiale')
        for n in request.form.get('student_list').replace(',', '\n').split('\n'):
            if n.strip(): db.sadd('lista_ufficiale', n.strip())
    return redirect(url_for('index'))

@app.route('/segna_presenza')
def segna_presenza():
    db.hset('presenze_oggi', session['username'], "OK")
    return redirect(url_for('index', presente=1))

@app.route('/add', methods=['POST'])
def add():
    db.rpush('competenze', f"{datetime.datetime.now().strftime('%H:%M')}|{session['username']}|{request.form.get('title')}|{request.form.get('content')}")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
