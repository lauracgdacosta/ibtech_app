import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import datetime

app = Flask(__name__)
app.secret_key = '18T3ch'

# --- MODELO DE TAREFAS PADRÃO PARA NOVOS PROJETOS ---
TAREFAS_PADRAO = [
    {'id': '1', 'desc': 'Planejamento', 'tipo': 'titulo'},
    {'id': '1.1', 'desc': 'Criar o cronograma do projeto', 'tipo': 'tarefa'},
    {'id': '1.2', 'desc': 'Validar o cronograma de projeto com equipe IBTECH', 'tipo': 'tarefa'},
    {'id': '1.3', 'desc': 'Aprovação do cronograma do projeto pelo o cliente', 'tipo': 'tarefa'},
    {'id': '2', 'desc': 'Execução', 'tipo': 'titulo'},
    {'id': '2.1', 'desc': 'Levantamento de requisitos', 'tipo': 'titulo'},
    {'id': '2.1.1', 'desc': 'Folha de pagamento', 'tipo': 'tarefa'},
    {'id': '2.1.2', 'desc': 'Contabilidade', 'tipo': 'tarefa'},
    {'id': '2.1.3', 'desc': 'Compras, licitações e contratos', 'tipo': 'tarefa'},
    {'id': '2.1.4', 'desc': 'Patrimônio', 'tipo': 'tarefa'},
    {'id': '2.1.5', 'desc': 'Almoxarifado', 'tipo': 'tarefa'},
    {'id': '2.1.6', 'desc': 'Frotas', 'tipo': 'tarefa'},
    {'id': '2.1.7', 'desc': 'Tributário', 'tipo': 'tarefa'},
    {'id': '2.1.8', 'desc': 'Nota Fiscal Eletrônica', 'tipo': 'tarefa'},
    {'id': '2.2', 'desc': 'Treinamento', 'tipo': 'titulo'},
    {'id': '2.2.1', 'desc': 'Folha de pagamento', 'tipo': 'tarefa'},
    {'id': '2.2.2', 'desc': 'Contabilidade', 'tipo': 'tarefa'},
    {'id': '2.2.3', 'desc': 'Compras, licitações e contratos', 'tipo': 'tarefa'},
    {'id': '2.2.4', 'desc': 'Patrimônio', 'tipo': 'tarefa'},
    {'id': '2.2.5', 'desc': 'Almoxarifado', 'tipo': 'tarefa'},
    {'id': '2.2.6', 'desc': 'Frotas', 'tipo': 'tarefa'},
    {'id': '2.2.7', 'desc': 'Tributário', 'tipo': 'tarefa'},
    {'id': '2.2.8', 'desc': 'Nota Fiscal Eletrônica', 'tipo': 'tarefa'},
    {'id': '2.3', 'desc': 'Paralisação dos Setores para Migração', 'tipo': 'titulo'},
    {'id': '2.3.1', 'desc': 'Suspensão temporária dos processos nos setores para realizar a migração e seus ajustes finais', 'tipo': 'tarefa'},
    {'id': '2.4', 'desc': 'Migração', 'tipo': 'titulo'},
    {'id': '2.4.1', 'desc': 'Folha de pagamento', 'tipo': 'tarefa'},
    {'id': '2.4.2', 'desc': 'Contabilidade', 'tipo': 'tarefa'},
    {'id': '2.4.3', 'desc': 'Compras, licitações e contratos', 'tipo': 'tarefa'},
    {'id': '2.4.4', 'desc': 'Patrimônio', 'tipo': 'tarefa'},
    {'id': '2.4.5', 'desc': 'Almoxarifado', 'tipo': 'tarefa'},
    {'id': '2.4.6', 'desc': 'Frotas', 'tipo': 'tarefa'},
    {'id': '2.4.7', 'desc': 'Tributário', 'tipo': 'tarefa'},
    {'id': '2.4.8', 'desc': 'Nota Fiscal Eletrônica', 'tipo': 'tarefa'},
    {'id': '2.5', 'desc': 'Validação e Ajustes Finais', 'tipo': 'titulo'},
    {'id': '2.5.1', 'desc': 'Folha de pagamento', 'tipo': 'tarefa'},
    {'id': '2.5.2', 'desc': 'Contabilidade', 'tipo': 'tarefa'},
    {'id': '2.5.3', 'desc': 'Compras, licitações e contratos', 'tipo': 'tarefa'},
    {'id': '2.5.4', 'desc': 'Patrimônio', 'tipo': 'tarefa'},
    {'id': '2.5.5', 'desc': 'Almoxarifado', 'tipo': 'tarefa'},
    {'id': '2.5.6', 'desc': 'Frotas', 'tipo': 'tarefa'},
    {'id': '2.5.7', 'desc': 'Tributário', 'tipo': 'tarefa'},
    {'id': '2.5.8', 'desc': 'Nota Fiscal Eletrônica', 'tipo': 'tarefa'},
    {'id': '3', 'desc': 'Go Live', 'tipo': 'titulo'},
    {'id': '3.1', 'desc': 'Iniciar utilização do GPI', 'tipo': 'tarefa'},
    {'id': '4', 'desc': 'Operação assistida', 'tipo': 'titulo'},
    {'id': '4.1', 'desc': 'Período onde os usuários poderão contar com suporte técnico contínuo', 'tipo': 'tarefa'},
    {'id': '4.2', 'desc': 'Envio do SICOM de agosto', 'tipo': 'tarefa'},
    {'id': '4.3', 'desc': 'Fechamento da folha de Setembro', 'tipo': 'tarefa'},
    {'id': '5', 'desc': 'Aceite da Implantação', 'tipo': 'titulo'},
    {'id': '5.1', 'desc': 'Receber o aceite da implantação', 'tipo': 'tarefa'},
]

# --- Filtro Jinja2 para Formatação de Data ---
def format_date(value):
    if value is None or value == "": return ""
    try: return datetime.datetime.strptime(value, '%Y-%m-%d').strftime('%d/%m/%Y')
    except ValueError:
        try: return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
        except ValueError: return value
app.jinja_env.filters['dateformat'] = format_date

# --- Configuração do Banco de Dados ---
def get_db_connection():
    conn = sqlite3.connect('/tmp/database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tecnicos (...)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (...)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS equipes (...)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pendencias (...)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ferias (...)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sistemas (...)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS agenda (...)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS prestacao_contas (...)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS projetos (...)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tarefas (...)''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nivel_acesso TEXT,
            role TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- SCRIPT DE MIGRAÇÃO DO BANCO DE DADOS ---
def migrate_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT role FROM usuarios LIMIT 1")
    except sqlite3.OperationalError:
        print("Executando migração: Adicionando coluna 'role' à tabela 'usuarios'.")
        cursor.execute("ALTER TABLE usuarios ADD COLUMN role TEXT")
    
    cursor.execute("""
        UPDATE usuarios 
        SET role = CASE 
            WHEN nivel_acesso = 'Admin' THEN 'admin'
            WHEN nivel_acesso = 'Usuario' THEN 'tecnico'
            ELSE 'tecnico'
        END
        WHERE role IS NULL
    """)
    
    cursor.execute("SELECT COUNT(id) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        hashed_senha = generate_password_hash("admin")
        cursor.execute("INSERT INTO usuarios (nome, email, senha, role) VALUES (?, ?, ?, ?)",
                       ('Administrador', 'admin@ibtech.com', hashed_senha, 'admin'))
        print("Nenhum usuário encontrado. Criado usuário 'admin@ibtech.com' com senha 'admin'.")
        
    conn.commit()
    conn.close()
    print("Migração do banco de dados concluída.")

with app.app_context():
    init_db()
    migrate_db()

# --- DECORADORES DE AUTENTICAÇÃO E AUTORIZAÇÃO ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('user_role') not in allowed_roles:
                flash('Você não tem permissão para acessar este recurso.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- ROTAS PRINCIPAIS E DE LOGIN/LOGOUT ---
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    hoje_str = datetime.date.today().strftime('%Y-%m-%d')
    proximos_agendamentos = conn.execute('SELECT * FROM agenda WHERE data_agendamento >= ? ORDER BY data_agendamento ASC LIMIT 5', (hoje_str,)).fetchall()
    pendencias_abertas = conn.execute("SELECT * FROM pendencias WHERE status = 'Aberto' ORDER BY data_prioridade ASC LIMIT 5").fetchall()
    tecnicos_em_ferias = conn.execute('SELECT * FROM ferias WHERE data_inicio <= ? AND data_termino >= ?', (hoje_str, hoje_str)).fetchall()
    conn.close()
    return render_template('index.html', proximos_agendamentos=proximos_agendamentos, pendencias_abertas=pendencias_abertas, tecnicos_em_ferias=tecnicos_em_ferias)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()
        if usuario and check_password_hash(usuario['senha'], senha):
            session['user_id'] = usuario['id']
            session['user_name'] = usuario['nome']
            session['user_role'] = usuario['role']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválidos.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# --- MÓDULOS DE CADASTRO (Admin, Coordenação) ---
@app.route('/cadastros')
@login_required
@role_required(['admin', 'coordenacao'])
def cadastros():
    return render_template('cadastros.html')

@app.route('/tecnicos')
@login_required
@role_required(['admin', 'coordenacao'])
def tecnicos():
    conn = get_db_connection()
    tecnicos_data = conn.execute('SELECT * FROM tecnicos').fetchall()
    conn.close()
    return render_template('tecnicos.html', tecnicos=tecnicos_data)

@app.route('/new_tecnico', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'coordenacao'])
def new_tecnico():
    # ... código original ...
    pass

@app.route('/edit_tecnico/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'coordenacao'])
def edit_tecnico(id):
    # ... código original ...
    pass

@app.route('/delete_tecnico/<int:id>', methods=['POST'])
@login_required
@role_required(['admin', 'coordenacao'])
def delete_tecnico(id):
    # ... código original ...
    pass

@app.route('/clientes')
@login_required
@role_required(['admin', 'coordenacao'])
def clientes():
    # ... código original ...
    pass

# E assim por diante para TODAS as rotas de Cadastros...

# --- MÓDULOS OPERACIONAIS (Admin, Coordenação, Técnico) ---

@app.route('/agenda')
@login_required
@role_required(['admin', 'coordenacao', 'tecnico'])
def agenda():
    # ... código original ...
    pass

@app.route('/projetos')
@login_required
@role_required(['admin', 'coordenacao', 'tecnico'])
def projetos():
    # ... código original ...
    pass

@app.route('/pendencias')
@login_required
@role_required(['admin', 'coordenacao', 'tecnico'])
def pendencias():
    # ... código original ...
    pass

# E assim por diante para TODAS as rotas operacionais e suas sub-rotas...

# --- MÓDULOS ADMINISTRATIVOS (Admin, Coordenação) ---

@app.route('/prestacao_contas')
@login_required
@role_required(['admin', 'coordenacao'])
def prestacao_contas():
    # ... código original ...
    pass

@app.route('/ferias')
@login_required
@role_required(['admin', 'coordenacao'])
def ferias():
    # ... código original ...
    pass

# --- GESTÃO DE USUÁRIOS (Somente Admin) ---

@app.route('/usuarios')
@login_required
@role_required(['admin'])
def usuarios():
    conn = get_db_connection()
    users_data = conn.execute('SELECT id, nome, email, role FROM usuarios').fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=users_data)

@app.route('/new_usuario', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def new_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        role = request.form['role']
        hashed_senha = generate_password_hash(senha)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nome, email, senha, role) VALUES (?, ?, ?, ?)',
                         (nome, email, hashed_senha, role))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Erro: O e-mail informado já existe.', 'danger')
            return redirect(url_for('new_usuario'))
        finally:
            conn.close()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('usuarios'))
    return render_template('new_usuario.html')

@app.route('/edit_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_usuario(id):
    conn = get_db_connection()
    usuario = conn.execute('SELECT id, nome, email, role FROM usuarios WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        role = request.form['role']
        senha = request.form.get('senha')
        try:
            if senha:
                hashed_senha = generate_password_hash(senha)
                conn.execute('UPDATE usuarios SET nome = ?, email = ?, role = ?, senha = ? WHERE id = ?',
                             (nome, email, role, hashed_senha, id))
            else:
                conn.execute('UPDATE usuarios SET nome = ?, email = ?, role = ? WHERE id = ?',
                             (nome, email, role, id))
            conn.commit()
            flash('Usuário atualizado com sucesso!', 'success')
        except sqlite3.IntegrityError:
            flash('Erro: O e-mail informado já pertence a outro usuário.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('usuarios'))
    conn.close()
    return render_template('edit_usuario.html', usuario=usuario)

@app.route('/delete_usuario/<int:id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_usuario(id):
    if id == session.get('user_id'):
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('usuarios'))
    conn = get_db_connection()
    conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('usuarios'))


if __name__ == '__main__':
    app.run(debug=True)