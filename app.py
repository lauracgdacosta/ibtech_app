import sqlite3
import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura_e_dificil_de_adivinhar'

# --- FILTRO DE DATA ---
def format_date(value):
    """Formata uma string de data AAAA-MM-DD para DD/MM/AAAA."""
    if value is None or value == "":
        return ""
    try:
        date_obj = datetime.datetime.strptime(value, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except ValueError:
        return value

app.jinja_env.filters['dateformat'] = format_date

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # --- CRIAÇÃO DAS TABELAS ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tecnicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT, telefone TEXT, funcao TEXT, equipe TEXT, contrato TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, municipio TEXT NOT NULL, orgao TEXT, contrato TEXT, sistemas TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, sigla TEXT, lider TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pendencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT, processo TEXT, cliente TEXT, sistema TEXT, data_prioridade TEXT, prazo_entrega TEXT, status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ferias (
            id INTEGER PRIMARY KEY AUTOINCREMENT, funcionario TEXT NOT NULL, admissao TEXT, contrato TEXT, ano INTEGER, data_inicio TEXT, data_termino TEXT, obs TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sistemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, sigla TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT NOT NULL, tecnico TEXT NOT NULL, sistema TEXT, data_agendamento DATE NOT NULL, motivo TEXT, descricao TEXT, status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, nivel_acesso TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prestacao_contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, sistema TEXT, responsavel TEXT, modulo TEXT, periodo TEXT, competencia TEXT, status TEXT, observacao TEXT, atualizado_por TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS implantacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, data_prevista TEXT, data_execucao TEXT, versao_sistema TEXT, responsavel_implantacao TEXT, status TEXT, tipo_implantacao TEXT, observacoes TEXT, atualizado_por TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atividades_implantacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT, implantacao_id INTEGER NOT NULL, grupo TEXT, atividade TEXT, data_inicio TEXT, data_termino TEXT, duracao TEXT, responsavel_pm TEXT, responsavel_cm TEXT, status TEXT, local_execucao TEXT, observacoes TEXT, FOREIGN KEY (implantacao_id) REFERENCES implantacoes (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

with app.app_context():
    init_db()

# --- DECORADOR DE LOGIN ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS PRINCIPAIS E DE AUTENTICAÇÃO ---
@app.route('/')
@login_required
def index():
    return render_template('index.html')

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
            session['user_level'] = usuario['nivel_acesso']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválidos.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# --- MÓDULO DE TÉCNICOS ---
@app.route('/tecnicos')
@login_required
def tecnicos():
    conn = get_db_connection()
    tecnicos_data = conn.execute('SELECT * FROM tecnicos').fetchall()
    conn.close()
    return render_template('tecnicos.html', tecnicos=tecnicos_data)

@app.route('/new_tecnico', methods=['GET', 'POST'])
@login_required
def new_tecnico():
    conn = get_db_connection()
    equipes = conn.execute('SELECT nome FROM equipes').fetchall()
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        funcao = request.form['funcao']
        equipe = request.form['equipe']
        contrato = request.form['contrato']
        conn.execute('INSERT INTO tecnicos (nome, email, telefone, funcao, equipe, contrato) VALUES (?, ?, ?, ?, ?, ?)',
                     (nome, email, telefone, funcao, equipe, contrato))
        conn.commit()
        conn.close()
        return redirect(url_for('tecnicos'))
    conn.close()
    return render_template('new_tecnico.html', equipes=equipes)

@app.route('/edit_tecnico/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tecnico(id):
    conn = get_db_connection()
    tecnico = conn.execute('SELECT * FROM tecnicos WHERE id = ?', (id,)).fetchone()
    equipes = conn.execute('SELECT nome FROM equipes').fetchall()
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        funcao = request.form['funcao']
        equipe = request.form['equipe']
        contrato = request.form['contrato']
        conn.execute('UPDATE tecnicos SET nome = ?, email = ?, telefone = ?, funcao = ?, equipe = ?, contrato = ? WHERE id = ?',
                     (nome, email, telefone, funcao, equipe, contrato, id))
        conn.commit()
        conn.close()
        return redirect(url_for('tecnicos'))
    conn.close()
    return render_template('edit_tecnico.html', tecnico=tecnico, equipes=equipes)

@app.route('/delete_tecnico/<int:id>', methods=['POST'])
@login_required
def delete_tecnico(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tecnicos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('tecnicos'))

# --- MÓDULO DE CLIENTES ---
@app.route('/clientes')
@login_required
def clientes():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT * FROM clientes').fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes_data)

@app.route('/new_cliente', methods=['GET', 'POST'])
@login_required
def new_cliente():
    conn = get_db_connection()
    sistemas_para_selecao = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas').fetchall()]
    if request.method == 'POST':
        municipio = request.form['municipio']
        orgao = request.form['orgao']
        contrato = request.form['contrato']
        sistemas = ', '.join(request.form.getlist('sistemas'))
        conn.execute('INSERT INTO clientes (municipio, orgao, contrato, sistemas) VALUES (?, ?, ?, ?)',
                     (municipio, orgao, contrato, sistemas))
        conn.commit()
        conn.close()
        return redirect(url_for('clientes'))
    conn.close()
    return render_template('new_cliente.html', sistemas_para_selecao=sistemas_para_selecao)

@app.route('/edit_cliente/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_cliente(id):
    conn = get_db_connection()
    cliente = conn.execute('SELECT * FROM clientes WHERE id = ?', (id,)).fetchone()
    sistemas_para_selecao = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas').fetchall()]
    sistemas_salvos = cliente['sistemas'].split(', ') if cliente['sistemas'] else []
    if request.method == 'POST':
        municipio = request.form['municipio']
        orgao = request.form['orgao']
        contrato = request.form['contrato']
        sistemas = ', '.join(request.form.getlist('sistemas'))
        conn.execute('UPDATE clientes SET municipio = ?, orgao = ?, contrato = ?, sistemas = ? WHERE id = ?',
                     (municipio, orgao, contrato, sistemas, id))
        conn.commit()
        conn.close()
        return redirect(url_for('clientes'))
    conn.close()
    return render_template('edit_cliente.html', cliente=cliente, sistemas_para_selecao=sistemas_para_selecao, sistemas_salvos=sistemas_salvos)

@app.route('/delete_cliente/<int:id>', methods=['POST'])
@login_required
def delete_cliente(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM clientes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('clientes'))

# --- MÓDULO DE EQUIPES ---
@app.route('/equipes')
@login_required
def equipes():
    conn = get_db_connection()
    equipes_data = conn.execute('SELECT * FROM equipes').fetchall()
    conn.close()
    return render_template('equipes.html', equipes=equipes_data)

@app.route('/new_equipe', methods=['GET', 'POST'])
@login_required
def new_equipe():
    conn = get_db_connection()
    tecnicos = conn.execute('SELECT nome FROM tecnicos').fetchall()
    if request.method == 'POST':
        nome = request.form['nome']
        sigla = request.form['sigla']
        lider = request.form['lider']
        conn.execute('INSERT INTO equipes (nome, sigla, lider) VALUES (?, ?, ?)', (nome, sigla, lider))
        conn.commit()
        conn.close()
        return redirect(url_for('equipes'))
    conn.close()
    return render_template('new_equipe.html', tecnicos=tecnicos)

@app.route('/edit_equipe/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_equipe(id):
    conn = get_db_connection()
    equipe = conn.execute('SELECT * FROM equipes WHERE id = ?', (id,)).fetchone()
    tecnicos = conn.execute('SELECT nome FROM tecnicos').fetchall()
    if request.method == 'POST':
        nome = request.form['nome']
        sigla = request.form['sigla']
        lider = request.form['lider']
        conn.execute('UPDATE equipes SET nome = ?, sigla = ?, lider = ? WHERE id = ?', (nome, sigla, lider, id))
        conn.commit()
        conn.close()
        return redirect(url_for('equipes'))
    conn.close()
    return render_template('edit_equipe.html', equipe=equipe, tecnicos=tecnicos)

@app.route('/delete_equipe/<int:id>', methods=['POST'])
@login_required
def delete_equipe(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM equipes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('equipes'))

# --- MÓDULO DE PENDÊNCIAS ---
@app.route('/pendencias')
@login_required
def pendencias():
    conn = get_db_connection()
    pendencias_data = conn.execute('SELECT * FROM pendencias').fetchall()
    conn.close()
    return render_template('pendencias.html', pendencias=pendencias_data)

@app.route('/new_pendencia', methods=['GET', 'POST'])
@login_required
def new_pendencia():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    sistemas_para_selecao = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas').fetchall()]
    if request.method == 'POST':
        processo = request.form['processo']
        cliente = request.form['cliente']
        sistema = request.form['sistema']
        data_prioridade = request.form['data_prioridade']
        prazo_entrega = request.form['prazo_entrega']
        status = request.form['status']
        conn.execute('INSERT INTO pendencias (processo, cliente, sistema, data_prioridade, prazo_entrega, status) VALUES (?, ?, ?, ?, ?, ?)',
                     (processo, cliente, sistema, data_prioridade, prazo_entrega, status))
        conn.commit()
        conn.close()
        return redirect(url_for('pendencias'))
    conn.close()
    return render_template('new_pendencia.html', clientes=clientes, sistemas_para_selecao=sistemas_para_selecao)

@app.route('/edit_pendencia/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_pendencia(id):
    conn = get_db_connection()
    pendencia = conn.execute('SELECT * FROM pendencias WHERE id = ?', (id,)).fetchone()
    if pendencia is None:
        conn.close()
        abort(404)
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    sistemas_para_selecao = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas').fetchall()]
    if request.method == 'POST':
        processo = request.form['processo']
        cliente = request.form['cliente'] 
        sistema = request.form['sistema']
        data_prioridade = request.form['data_prioridade']
        prazo_entrega = request.form['prazo_entrega']
        status = request.form['status']
        conn.execute('UPDATE pendencias SET processo = ?, cliente = ?, sistema = ?, data_prioridade = ?, prazo_entrega = ?, status = ? WHERE id = ?',
                     (processo, cliente, sistema, data_prioridade, prazo_entrega, status, id))
        conn.commit()
        conn.close()
        return redirect(url_for('pendencias'))
    conn.close()
    return render_template('edit_pendencia.html', pendencia=pendencia, clientes=clientes, sistemas_para_selecao=sistemas_para_selecao)

@app.route('/delete_pendencia/<int:id>', methods=['POST'])
@login_required
def delete_pendencia(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM pendencias WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('pendencias'))

# --- MÓDULO DE FÉRIAS ---
@app.route('/ferias')
@login_required
def ferias():
    conn = get_db_connection()
    ferias_data = conn.execute('SELECT * FROM ferias').fetchall()
    conn.close()
    return render_template('ferias.html', ferias=ferias_data)

@app.route('/new_ferias', methods=['GET', 'POST'])
@login_required
def new_ferias():
    conn = get_db_connection()
    tecnicos_data = conn.execute('SELECT nome, contrato FROM tecnicos').fetchall()
    tecnicos = [(t['nome'], t['contrato']) for t in tecnicos_data]
    if request.method == 'POST':
        funcionario = request.form['funcionario']
        admissao = request.form['admissao']
        contrato = request.form['contrato']
        ano = request.form['ano']
        data_inicio = request.form['data_inicio']
        data_termino = request.form['data_termino']
        obs = request.form['obs']
        conn.execute('INSERT INTO ferias (funcionario, admissao, contrato, ano, data_inicio, data_termino, obs) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (funcionario, admissao, contrato, ano, data_inicio, data_termino, obs))
        conn.commit()
        conn.close()
        return redirect(url_for('ferias'))
    conn.close()
    return render_template('new_ferias.html', tecnicos=tecnicos)

@app.route('/edit_ferias/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_ferias(id):
    conn = get_db_connection()
    ferias_item = conn.execute('SELECT * FROM ferias WHERE id = ?', (id,)).fetchone()
    tecnicos_data = conn.execute('SELECT nome, contrato FROM tecnicos').fetchall()
    tecnicos = [(t['nome'], t['contrato']) for t in tecnicos_data]
    if request.method == 'POST':
        funcionario = request.form['funcionario']
        admissao = request.form['admissao']
        contrato = request.form['contrato']
        ano = request.form['ano']
        data_inicio = request.form['data_inicio']
        data_termino = request.form['data_termino']
        obs = request.form['obs']
        conn.execute('UPDATE ferias SET funcionario = ?, admissao = ?, contrato = ?, ano = ?, data_inicio = ?, data_termino = ?, obs = ? WHERE id = ?',
                     (funcionario, admissao, contrato, ano, data_inicio, data_termino, obs, id))
        conn.commit()
        conn.close()
        return redirect(url_for('ferias'))
    conn.close()
    return render_template('edit_ferias.html', ferias_item=ferias_item, tecnicos=tecnicos)

@app.route('/delete_ferias/<int:id>', methods=['POST'])
@login_required
def delete_ferias(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM ferias WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('ferias'))

# --- MÓDULO DE SISTEMAS ---
@app.route('/sistemas')
@login_required
def sistemas():
    conn = get_db_connection()
    sistemas_data = conn.execute('SELECT * FROM sistemas').fetchall()
    conn.close()
    return render_template('sistemas.html', sistemas=sistemas_data)

@app.route('/new_sistema', methods=['GET', 'POST'])
@login_required
def new_sistema():
    if request.method == 'POST':
        conn = get_db_connection()
        nome = request.form['nome']
        sigla = request.form['sigla']
        conn.execute('INSERT INTO sistemas (nome, sigla) VALUES (?, ?)', (nome, sigla))
        conn.commit()
        conn.close()
        return redirect(url_for('sistemas'))
    return render_template('new_sistema.html')

@app.route('/edit_sistema/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_sistema(id):
    conn = get_db_connection()
    sistema = conn.execute('SELECT * FROM sistemas WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        nome = request.form['nome']
        sigla = request.form['sigla']
        conn.execute('UPDATE sistemas SET nome = ?, sigla = ? WHERE id = ?', (nome, sigla, id))
        conn.commit()
        conn.close()
        return redirect(url_for('sistemas'))
    conn.close()
    return render_template('edit_sistema.html', sistema=sistema)

@app.route('/delete_sistema/<int:id>', methods=['POST'])
@login_required
def delete_sistema(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM sistemas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('sistemas'))

# --- MÓDULO DE AGENDA ---
@app.route('/agenda')
@login_required
def agenda():
    conn = get_db_connection()
    agenda_data = conn.execute('SELECT * FROM agenda ORDER BY data_agendamento DESC').fetchall()
    conn.close()
    return render_template('agenda.html', agenda_data=agenda_data)

@app.route('/new_agenda', methods=['GET', 'POST'])
@login_required
def new_agenda():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    tecnicos = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    if request.method == 'POST':
        cliente = request.form['cliente']
        tecnico = request.form['tecnico']
        sistema = request.form['sistema']
        data_agendamento = request.form['data_agendamento']
        motivo = request.form['motivo']
        descricao = request.form['descricao']
        status = request.form['status']
        conn.execute('INSERT INTO agenda (cliente, tecnico, sistema, data_agendamento, motivo, descricao, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (cliente, tecnico, sistema, data_agendamento, motivo, descricao, status))
        conn.commit()
        conn.close()
        return redirect(url_for('agenda'))
    conn.close()
    return render_template('new_agenda.html', clientes=clientes, tecnicos=tecnicos, sistemas=sistemas)

@app.route('/edit_agenda/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_agenda(id):
    conn = get_db_connection()
    agendamento = conn.execute('SELECT * FROM agenda WHERE id = ?', (id,)).fetchone()
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    tecnicos = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    if request.method == 'POST':
        cliente = request.form['cliente']
        tecnico = request.form['tecnico']
        sistema = request.form['sistema']
        data_agendamento = request.form['data_agendamento']
        motivo = request.form['motivo']
        descricao = request.form['descricao']
        status = request.form['status']
        conn.execute('UPDATE agenda SET cliente = ?, tecnico = ?, sistema = ?, data_agendamento = ?, motivo = ?, descricao = ?, status = ? WHERE id = ?',
                     (cliente, tecnico, sistema, data_agendamento, motivo, descricao, status, id))
        conn.commit()
        conn.close()
        return redirect(url_for('agenda'))
    conn.close()
    return render_template('edit_agenda.html', agendamento=agendamento, clientes=clientes, tecnicos=tecnicos, sistemas=sistemas)

@app.route('/delete_agenda/<int:id>', methods=['POST'])
@login_required
def delete_agenda(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM agenda WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('agenda'))

# --- MÓDULO DE USUÁRIOS ---
@app.route('/usuarios')
@login_required
def usuarios():
    conn = get_db_connection()
    users_data = conn.execute('SELECT id, nome, email, nivel_acesso FROM usuarios').fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=users_data)

@app.route('/new_usuario', methods=['GET', 'POST'])
@login_required
def new_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        nivel_acesso = request.form['nivel_acesso']
        hashed_senha = generate_password_hash(senha)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nome, email, senha, nivel_acesso) VALUES (?, ?, ?, ?)',
                         (nome, email, hashed_senha, nivel_acesso))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash('Erro: O e-mail informado já existe.', 'danger')
            return redirect(url_for('new_usuario'))
        finally:
            conn.close()
        return redirect(url_for('usuarios'))
    return render_template('new_usuario.html')

@app.route('/edit_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_usuario(id):
    conn = get_db_connection()
    usuario = conn.execute('SELECT id, nome, email, nivel_acesso FROM usuarios WHERE id = ?', (id,)).fetchone()
    if usuario is None:
        conn.close()
        abort(404)
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        nivel_acesso = request.form['nivel_acesso']
        senha = request.form.get('senha')
        if senha:
            hashed_senha = generate_password_hash(senha)
            conn.execute('UPDATE usuarios SET nome = ?, email = ?, nivel_acesso = ?, senha = ? WHERE id = ?',
                         (nome, email, nivel_acesso, hashed_senha, id))
        else:
            conn.execute('UPDATE usuarios SET nome = ?, email = ?, nivel_acesso = ? WHERE id = ?',
                         (nome, email, nivel_acesso, id))
        conn.commit()
        conn.close()
        return redirect(url_for('usuarios'))
    conn.close()
    return render_template('edit_usuario.html', usuario=usuario)

@app.route('/delete_usuario/<int:id>', methods=['POST'])
@login_required
def delete_usuario(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('usuarios'))

# --- MÓDULO DE PRESTAÇÃO DE CONTAS ---
@app.route('/prestacao_contas')
@login_required
def prestacao_contas():
    conn = get_db_connection()
    dados = conn.execute('SELECT * FROM prestacao_contas ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('prestacao_contas.html', dados=dados)

@app.route('/new_prestacao', methods=['GET', 'POST'])
@login_required
def new_prestacao():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    if request.method == 'POST':
        cliente = request.form['cliente']
        sistema = request.form['sistema']
        responsavel = request.form['responsavel']
        modulo = request.form['modulo']
        periodo = request.form['periodo']
        competencia = request.form['competencia']
        status = request.form['status']
        observacao = request.form['observacao']
        timestamp = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        usuario_logado = session.get('user_name', 'Desconhecido')
        atualizado_por = f"{timestamp} por {usuario_logado}"
        conn.execute(
            'INSERT INTO prestacao_contas (cliente, sistema, responsavel, modulo, periodo, competencia, status, observacao, atualizado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (cliente, sistema, responsavel, modulo, periodo, competencia, status, observacao, atualizado_por)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('prestacao_contas'))
    conn.close()
    return render_template('new_prestacao.html', clientes=clientes, sistemas=sistemas, responsaveis=responsaveis)

@app.route('/edit_prestacao/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_prestacao(id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM prestacao_contas WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        cliente = request.form['cliente']
        sistema = request.form['sistema']
        responsavel = request.form['responsavel']
        modulo = request.form['modulo']
        periodo = request.form['periodo']
        competencia = request.form['competencia']
        status = request.form['status']
        observacao = request.form['observacao']
        timestamp = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        usuario_logado = session.get('user_name', 'Desconhecido')
        atualizado_por = f"{timestamp} por {usuario_logado}"
        conn.execute(
            'UPDATE prestacao_contas SET cliente = ?, sistema = ?, responsavel = ?, modulo = ?, periodo = ?, competencia = ?, status = ?, observacao = ?, atualizado_por = ? WHERE id = ?',
            (cliente, sistema, responsavel, modulo, periodo, competencia, status, observacao, atualizado_por, id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('prestacao_contas'))
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    conn.close()
    return render_template('edit_prestacao.html', item=item, clientes=clientes, sistemas=sistemas, responsaveis=responsaveis)

@app.route('/delete_prestacao/<int:id>', methods=['POST'])
@login_required
def delete_prestacao(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM prestacao_contas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('prestacao_contas'))

# --- MÓDULO DE IMPLANTAÇÃO E CHECKLIST ---
@app.route('/implantacoes')
@login_required
def implantacoes():
    conn = get_db_connection()
    dados = conn.execute('SELECT * FROM implantacoes ORDER BY data_prevista DESC').fetchall()
    conn.close()
    return render_template('implantacoes.html', dados=dados)

@app.route('/new_implantacao', methods=['GET', 'POST'])
@login_required
def new_implantacao():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    if request.method == 'POST':
        cliente = request.form['cliente']
        data_prevista = request.form['data_prevista']
        data_execucao = request.form['data_execucao']
        versao_sistema = request.form['versao_sistema']
        responsavel_implantacao = request.form['responsavel_implantacao']
        status = request.form['status']
        tipo_implantacao = request.form['tipo_implantacao']
        observacoes = request.form['observacoes']
        timestamp = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        usuario_logado = session.get('user_name', 'Desconhecido')
        atualizado_por = f"{timestamp} por {usuario_logado}"
        conn.execute(
            'INSERT INTO implantacoes (cliente, data_prevista, data_execucao, versao_sistema, responsavel_implantacao, status, tipo_implantacao, observacoes, atualizado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (cliente, data_prevista, data_execucao, versao_sistema, responsavel_implantacao, status, tipo_implantacao, observacoes, atualizado_por)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('implantacoes'))
    conn.close()
    return render_template('new_implantacao.html', clientes=clientes, responsaveis=responsaveis)

@app.route('/edit_implantacao/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_implantacao(id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM implantacoes WHERE id = ?', (id,)).fetchone()
    if item is None:
        conn.close()
        abort(404)
    if request.method == 'POST':
        cliente = request.form['cliente']
        data_prevista = request.form['data_prevista']
        data_execucao = request.form['data_execucao']
        versao_sistema = request.form['versao_sistema']
        responsavel_implantacao = request.form['responsavel_implantacao']
        status = request.form['status']
        tipo_implantacao = request.form['tipo_implantacao']
        observacoes = request.form['observacoes']
        timestamp = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        usuario_logado = session.get('user_name', 'Desconhecido')
        atualizado_por = f"{timestamp} por {usuario_logado}"
        conn.execute(
            'UPDATE implantacoes SET cliente = ?, data_prevista = ?, data_execucao = ?, versao_sistema = ?, responsavel_implantacao = ?, status = ?, tipo_implantacao = ?, observacoes = ?, atualizado_por = ? WHERE id = ?',
            (cliente, data_prevista, data_execucao, versao_sistema, responsavel_implantacao, status, tipo_implantacao, observacoes, atualizado_por, id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('implantacoes'))
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    conn.close()
    return render_template('edit_implantacao.html', item=item, clientes=clientes, responsaveis=responsaveis)

@app.route('/delete_implantacao/<int:id>', methods=['POST'])
@login_required
def delete_implantacao(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM implantacoes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('implantacoes'))

CHECKLIST_PADRAO = [
    {'grupo': 'Planejamento', 'atividade': 'Criar o cronograma do projeto'},
    {'grupo': 'Planejamento', 'atividade': 'Validar o cronograma de projeto com equipe IBTECH'},
    {'grupo': 'Planejamento', 'atividade': 'Aprovação do cronograma do projeto pelo o cliente'},
    {'grupo': 'Execução', 'atividade': 'Levantamento de requisitos - Folha de pagamento'},
    {'grupo': 'Execução', 'atividade': 'Levantamento de requisitos - Contabilidade'},
    {'grupo': 'Execução', 'atividade': 'Levantamento de requisitos - Compras, licitações e contratos'},
    {'grupo': 'Execução', 'atividade': 'Levantamento de requisitos - Patrimônio'},
    {'grupo': 'Execução', 'atividade': 'Levantamento de requisitos - Almoxarifado'},
    {'grupo': 'Execução', 'atividade': 'Levantamento de requisitos - Frotas'},
    {'grupo': 'Execução', 'atividade': 'Levantamento de requisitos - Tributário'},
    {'grupo': 'Execução', 'atividade': 'Levantamento de requisitos - Nota Fiscal Eletrônica'},
    {'grupo': 'Treinamento', 'atividade': 'Treinamento - Folha de pagamento'},
    {'grupo': 'Treinamento', 'atividade': 'Treinamento - Contabilidade'},
    {'grupo': 'Treinamento', 'atividade': 'Treinamento - Compras, licitações e contratos'},
    {'grupo': 'Treinamento', 'atividade': 'Treinamento - Patrimônio'},
    {'grupo': 'Treinamento', 'atividade': 'Treinamento - Almoxarifado'},
    {'grupo': 'Treinamento', 'atividade': 'Treinamento - Frotas'},
    {'grupo': 'Paralisação dos Setores para Migração', 'atividade': 'Suspensão temporária dos processos nos setores para realizar a migração e seus ajustes finais'},
    {'grupo': 'Migração', 'atividade': 'Migração - Folha de pagamento'},
    {'grupo': 'Migração', 'atividade': 'Migração - Contabilidade'},
    {'grupo': 'Migração', 'atividade': 'Migração - Compras, licitações e contratos'},
    {'grupo': 'Migração', 'atividade': 'Migração - Patrimônio'},
    {'grupo': 'Migração', 'atividade': 'Migração - Almoxarifado'},
    {'grupo': 'Migração', 'atividade': 'Migração - Frotas'},
    {'grupo': 'Validação e Ajustes Finais', 'atividade': 'Validação - Folha de pagamento'},
    {'grupo': 'Validação e Ajustes Finais', 'atividade': 'Validação - Contabilidade'},
    {'grupo': 'Validação e Ajustes Finais', 'atividade': 'Validação - Compras, licitações e contratos'},
    {'grupo': 'Validação e Ajustes Finais', 'atividade': 'Validação - Patrimônio'},
    {'grupo': 'Validação e Ajustes Finais', 'atividade': 'Validação - Almoxarifado'},
    {'grupo': 'Validação e Ajustes Finais', 'atividade': 'Validação - Frotas'},
    {'grupo': 'Go Live', 'atividade': 'Iniciar utilização do GPI'},
    {'grupo': 'Go Live', 'atividade': 'Operação assistida: Período onde os usuários poderão contar com suporte técnico contínuo'},
    {'grupo': 'Go Live', 'atividade': 'Envio do SICOM de agosto'},
    {'grupo': 'Go Live', 'atividade': 'Fechamento da folha de Setembro'},
    {'grupo': 'Aceite da Implantação', 'atividade': 'Receber o aceite da implantação'},
]

@app.route('/implantacao/<int:implantacao_id>/checklist', methods=['GET', 'POST'])
@login_required
def gerenciar_checklist(implantacao_id):
    conn = get_db_connection()
    if request.method == 'POST':
        for atividade_id in request.form.getlist('atividade_id'):
            data_inicio = request.form.get(f'data_inicio_{atividade_id}')
            data_termino = request.form.get(f'data_termino_{atividade_id}')
            duracao = request.form.get(f'duracao_{atividade_id}')
            responsavel_pm = request.form.get(f'responsavel_pm_{atividade_id}')
            responsavel_cm = request.form.get(f'responsavel_cm_{atividade_id}')
            status = request.form.get(f'status_{atividade_id}')
            local_execucao = request.form.get(f'local_execucao_{atividade_id}')
            observacoes = request.form.get(f'observacoes_{atividade_id}')
            conn.execute(
                'UPDATE atividades_implantacao SET data_inicio=?, data_termino=?, duracao=?, responsavel_pm=?, responsavel_cm=?, status=?, local_execucao=?, observacoes=? WHERE id=?',
                (data_inicio, data_termino, duracao, responsavel_pm, responsavel_cm, status, local_execucao, observacoes, atividade_id)
            )
        conn.commit()
        flash('Checklist atualizado com sucesso!', 'success')
    implantacao = conn.execute('SELECT * FROM implantacoes WHERE id = ?', (implantacao_id,)).fetchone()
    if not implantacao:
        conn.close()
        abort(404)
    atividades = conn.execute('SELECT * FROM atividades_implantacao WHERE implantacao_id = ? ORDER BY id', (implantacao_id,)).fetchall()
    if not atividades:
        for item in CHECKLIST_PADRAO:
            conn.execute(
                'INSERT INTO atividades_implantacao (implantacao_id, grupo, atividade, status) VALUES (?, ?, ?, ?)',
                (implantacao_id, item['grupo'], item['atividade'], 'Pendente')
            )
        conn.commit()
        atividades = conn.execute('SELECT * FROM atividades_implantacao WHERE implantacao_id = ? ORDER BY id', (implantacao_id,)).fetchall()
    conn.close()
    return render_template('checklist_implantacao.html', implantacao=implantacao, atividades=atividades)

# --- INICIALIZAÇÃO DA APLICAÇÃO ---
if __name__ == '__main__':
    app.run(debug=True)