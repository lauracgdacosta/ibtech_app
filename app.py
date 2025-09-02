import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps


app = Flask(__name__)

app.secret_key = '18T3ch'


# Configuração do banco de dados
def init_db():
    conn = sqlite3.connect('/tmp/database.db')
    cursor = conn.cursor()
    
    # Criação das tabelas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tecnicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT,
            telefone TEXT,
            funcao TEXT,
            equipe TEXT,
            contrato TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            municipio TEXT NOT NULL,
            orgao TEXT,
            contrato TEXT,
            sistemas TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            sigla TEXT,
            lider TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cronogramas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipe TEXT,
            tecnico_nome TEXT,
            tecnico_funcao TEXT,
            atividade_segunda TEXT,
            atividade_terca TEXT,
            atividade_quarta TEXT,
            atividade_quinta TEXT,
            atividade_sexta TEXT,
            atividade_sabado TEXT,
            atividade_domingo TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            localidade_orgao TEXT,
            data_1a_rodada TEXT,
            equipe_1 TEXT,
            tecnico_1 TEXT,
            data_2a_rodada TEXT,
            equipe_2 TEXT,
            tecnico_2 TEXT,
            status_2a_rodada TEXT,
            data_3a_rodada TEXT,
            equipe_3 TEXT,
            tecnico_3 TEXT,
            status_3a_rodada TEXT,
            data_4a_rodada TEXT,
            equipe_4 TEXT,
            tecnico_4 TEXT,
            status_4a_rodada TEXT,
            obs TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pendencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processo TEXT,
            cliente TEXT,
            sistema TEXT,
            data_prioridade TEXT,
            prazo_entrega TEXT,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ferias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            funcionario TEXT NOT NULL,
            admissao TEXT,
            contrato TEXT,
            ano INTEGER,
            data_inicio TEXT,
            data_termino TEXT,
            obs TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sistemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            sigla TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            tecnico TEXT NOT NULL,
            sistema TEXT,
            data_agendamento DATE NOT NULL,
            motivo TEXT,
            descricao TEXT,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nivel_acesso TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('/tmp/database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Inicializar o banco de dados no início da aplicação
with app.app_context():
    init_db()

@app.route('/')
def index():
    return render_template('index.html')

# Rotas do Módulo de Técnicos
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

# Rotas do Módulo de Clientes
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

# Rotas do Módulo de Equipes
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

# Rotas do Módulo de Cronograma
@app.route('/cronograma')
@login_required
def cronograma():
    conn = get_db_connection()
    cronogramas_data = conn.execute('SELECT * FROM cronogramas').fetchall()
    conn.close()
    return render_template('cronograma.html', cronogramas=cronogramas_data)

@app.route('/new_cronograma', methods=['GET', 'POST'])
@login_required
def new_cronograma():
    if request.method == 'POST':
        conn = get_db_connection()
        equipe = request.form['equipe']
        tecnico_nome = request.form['tecnico_nome']
        tecnico_funcao = request.form['tecnico_funcao']
        atividade_domingo = request.form['atividade_domingo']
        atividade_segunda = request.form['atividade_segunda']
        atividade_terca = request.form['atividade_terca']
        atividade_quarta = request.form['atividade_quarta']
        atividade_quinta = request.form['atividade_quinta']
        atividade_sexta = request.form['atividade_sexta']
        atividade_sabado = request.form['atividade_sabado']
        conn.execute('INSERT INTO cronogramas (equipe, tecnico_nome, tecnico_funcao, atividade_domingo, atividade_segunda, atividade_terca, atividade_quarta, atividade_quinta, atividade_sexta, atividade_sabado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (equipe, tecnico_nome, tecnico_funcao, atividade_domingo, atividade_segunda, atividade_terca, atividade_quarta, atividade_quinta, atividade_sexta, atividade_sabado))
        conn.commit()
        conn.close()
        return redirect(url_for('cronograma'))
    return render_template('new_cronograma.html')

@app.route('/edit_cronograma/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_cronograma(id):
    conn = get_db_connection()
    cronograma_item = conn.execute('SELECT * FROM cronogramas WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        equipe = request.form['equipe']
        tecnico_nome = request.form['tecnico_nome']
        tecnico_funcao = request.form['tecnico_funcao']
        atividade_domingo = request.form['atividade_domingo']
        atividade_segunda = request.form['atividade_segunda']
        atividade_terca = request.form['atividade_terca']
        atividade_quarta = request.form['atividade_quarta']
        atividade_quinta = request.form['atividade_quinta']
        atividade_sexta = request.form['atividade_sexta']
        atividade_sabado = request.form['atividade_sabado']
        conn.execute('UPDATE cronogramas SET equipe = ?, tecnico_nome = ?, tecnico_funcao = ?, atividade_domingo = ?, atividade_segunda = ?, atividade_terca = ?, atividade_quarta = ?, atividade_quinta = ?, atividade_sexta = ?, atividade_sabado = ? WHERE id = ?',
                     (equipe, tecnico_nome, tecnico_funcao, atividade_domingo, atividade_segunda, atividade_terca, atividade_quarta, atividade_quinta, atividade_sexta, atividade_sabado, id))
        conn.commit()
        conn.close()
        return redirect(url_for('cronograma'))
    conn.close()
    return render_template('edit_cronograma.html', cronograma_item=cronograma_item)

@app.route('/delete_cronograma/<int:id>', methods=['POST'])
@login_required
def delete_cronograma(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM cronogramas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('cronograma'))

# Rotas do Módulo de Visitas
@app.route('/visitas')
@login_required
def visitas():
    conn = get_db_connection()
    visitas_data = conn.execute('SELECT * FROM visitas').fetchall()
    conn.close()
    return render_template('visitas.html', visitas=visitas_data)

@app.route('/new_visita', methods=['GET', 'POST'])
@login_required
def new_visita():
    conn = get_db_connection()
    clientes = [row['orgao'] for row in conn.execute('SELECT orgao FROM clientes').fetchall()]
    equipes = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
    tecnicos = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos').fetchall()]

    if request.method == 'POST':
        localidade_orgao = request.form['localidade_orgao']
        data_1a_rodada = request.form['data_1a_rodada']
        equipe_1 = request.form['equipe_1']
        tecnico_1 = request.form['tecnico_1']
        data_2a_rodada = request.form['data_2a_rodada']
        equipe_2 = request.form['equipe_2']
        tecnico_2 = request.form['tecnico_2']
        status_2a_rodada = request.form['status_2a_rodada']
        data_3a_rodada = request.form.get('data_3a_rodada')
        equipe_3 = request.form.get('equipe_3')
        tecnico_3 = request.form.get('tecnico_3')
        status_3a_rodada = request.form.get('status_3a_rodada')
        data_4a_rodada = request.form.get('data_4a_rodada')
        equipe_4 = request.form.get('equipe_4')
        tecnico_4 = request.form.get('tecnico_4')
        status_4a_rodada = request.form.get('status_4a_rodada')
        obs = request.form.get('obs')

        conn.execute('INSERT INTO visitas (localidade_orgao, data_1a_rodada, equipe_1, tecnico_1, data_2a_rodada, equipe_2, tecnico_2, status_2a_rodada, data_3a_rodada, equipe_3, tecnico_3, status_3a_rodada, data_4a_rodada, equipe_4, tecnico_4, status_4a_rodada, obs) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (localidade_orgao, data_1a_rodada, equipe_1, tecnico_1, data_2a_rodada, equipe_2, tecnico_2, status_2a_rodada, data_3a_rodada, equipe_3, tecnico_3, status_3a_rodada, data_4a_rodada, equipe_4, tecnico_4, status_4a_rodada, obs))
        conn.commit()
        conn.close()
        return redirect(url_for('visitas'))
    
    conn.close()
    return render_template('new_visita.html', clientes=clientes, equipes=equipes, tecnicos=tecnicos)

@app.route('/edit_visita/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_visita(id):
    conn = get_db_connection()
    visita = conn.execute('SELECT * FROM visitas WHERE id = ?', (id,)).fetchone()
    clientes = [row['orgao'] for row in conn.execute('SELECT orgao FROM clientes').fetchall()]
    equipes = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
    tecnicos = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos').fetchall()]
    
    if request.method == 'POST':
        localidade_orgao = request.form['localidade_orgao']
        data_1a_rodada = request.form['data_1a_rodada']
        equipe_1 = request.form['equipe_1']
        tecnico_1 = request.form['tecnico_1']
        data_2a_rodada = request.form['data_2a_rodada']
        equipe_2 = request.form['equipe_2']
        tecnico_2 = request.form['tecnico_2']
        status_2a_rodada = request.form['status_2a_rodada']
        data_3a_rodada = request.form.get('data_3a_rodada')
        equipe_3 = request.form.get('equipe_3')
        tecnico_3 = request.form.get('tecnico_3')
        status_3a_rodada = request.form.get('status_3a_rodada')
        data_4a_rodada = request.form.get('data_4a_rodada')
        equipe_4 = request.form.get('equipe_4')
        tecnico_4 = request.form.get('tecnico_4')
        status_4a_rodada = request.form.get('status_4a_rodada')
        obs = request.form.get('obs')

        conn.execute('UPDATE visitas SET localidade_orgao = ?, data_1a_rodada = ?, equipe_1 = ?, tecnico_1 = ?, data_2a_rodada = ?, equipe_2 = ?, tecnico_2 = ?, status_2a_rodada = ?, data_3a_rodada = ?, equipe_3 = ?, tecnico_3 = ?, status_3a_rodada = ?, data_4a_rodada = ?, equipe_4 = ?, tecnico_4 = ?, status_4a_rodada = ?, obs = ? WHERE id = ?',
                     (localidade_orgao, data_1a_rodada, equipe_1, tecnico_1, data_2a_rodada, equipe_2, tecnico_2, status_2a_rodada, data_3a_rodada, equipe_3, tecnico_3, status_3a_rodada, data_4a_rodada, equipe_4, tecnico_4, status_4a_rodada, obs, id))
        conn.commit()
        conn.close()
        return redirect(url_for('visitas'))
    
    conn.close()
    return render_template('edit_visita.html', visita=visita, clientes=clientes, equipes=equipes, tecnicos=tecnicos)

@app.route('/delete_visita/<int:id>', methods=['POST'])
@login_required
def delete_visita(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM visitas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('visitas'))

# Rotas do Módulo de Pendências
@app.route('/pendencias')
@login_required
def pendencias():
    conn = get_db_connection()
    pendencias_data = conn.execute('SELECT * FROM pendencias').fetchall()
    conn.close()
    return render_template('pendencias.html', pendencias=pendencias_data)

# Trecho do arquivo app.py
@app.route('/new_pendencia', methods=['GET', 'POST'])
@login_required
def new_pendencia():
    conn = get_db_connection()
    # Modificado para buscar municipio e orgao e concatenar
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    sistemas_para_selecao = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas').fetchall()]
    if request.method == 'POST':
        processo = request.form['processo']
        cliente = request.form['cliente'] # cliente já virá como "município - órgão"
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
    clientes = [row['orgao'] for row in conn.execute('SELECT orgao FROM clientes').fetchall()]
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
    
# Rotas do Módulo de Férias
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

# Rotas do Módulo de Sistemas
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

# Rotas do Módulo de Agenda

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
    
    # Busca dados para os seletores do formulário
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

    # Busca dados para os seletores do formulário
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

# Rotas do Módulo de Gestão de Usuários

@app.route('/usuarios')
@login_required
def usuarios():
    conn = get_db_connection()
    # Excluindo a senha da consulta para não a expor desnecessariamente
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

        # Gerar o hash da senha
        hashed_senha = generate_password_hash(senha)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nome, email, senha, nivel_acesso) VALUES (?, ?, ?, ?)',
                         (nome, email, hashed_senha, nivel_acesso))
            conn.commit()
        except sqlite3.IntegrityError:
            # Lidar com o caso de email duplicado
            conn.close()
            # Aqui você poderia retornar uma mensagem de erro para o template
            return "Erro: O e-mail informado já existe.", 400
        finally:
            conn.close()

        return redirect(url_for('usuarios'))
    
    return render_template('new_usuario.html')

@app.route('/edit_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_usuario(id):
    conn = get_db_connection()
    # Buscando sem a senha
    usuario = conn.execute('SELECT id, nome, email, nivel_acesso FROM usuarios WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        nivel_acesso = request.form['nivel_acesso']
        senha = request.form.get('senha') # Pega a senha, pode ser vazia

        if senha:
            # Se uma nova senha foi fornecida, atualiza o hash
            hashed_senha = generate_password_hash(senha)
            conn.execute('UPDATE usuarios SET nome = ?, email = ?, nivel_acesso = ?, senha = ? WHERE id = ?',
                         (nome, email, nivel_acesso, hashed_senha, id))
        else:
            # Caso contrário, mantém a senha antiga
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
    # Adicionar verificação para não permitir que o usuário se auto-delete ou delete o admin principal
    # (Isso seria uma lógica mais avançada de sessão)
    conn = get_db_connection()
    conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('usuarios'))

# Rotas de Autenticação

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário já estiver logado, redireciona para a home
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()

        if usuario and check_password_hash(usuario['senha'], senha):
            # Login bem-sucedido, armazena dados na sessão
            session['user_id'] = usuario['id']
            session['user_name'] = usuario['nome']
            session['user_level'] = usuario['nivel_acesso']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            # Falha no login
            flash('Email ou senha inválidos.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear() # Limpa todos os dados da sessão
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # A linha abaixo irá iniciar o servidor em modo de depuração.
    # Isso mostrará erros detalhados no navegador.
    # Lembre-se de desativar (debug=False) antes de colocar em produção!
    app.run(debug=True)