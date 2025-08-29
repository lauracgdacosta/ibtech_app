import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

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
            equipe_2 TEXT,
            tecnico_2 TEXT,
            data_2a_rodada TEXT,
            equipe_3 TEXT,
            tecnico_3 TEXT,
            equipe_4 TEXT,
            tecnico_4 TEXT,
            status_1a_rodada TEXT,
            status_2a_rodada TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pendencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processo TEXT NOT NULL,
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

    # Migração da tabela visitas
    cursor.execute("PRAGMA table_info(visitas)")
    columns_visitas = [col[1] for col in cursor.fetchall()]
    
    if 'status_1a_rodada' not in columns_visitas:
        cursor.execute("ALTER TABLE visitas ADD COLUMN status_1a_rodada TEXT DEFAULT 'Planejada'")
    if 'status_2a_rodada' not in columns_visitas:
        cursor.execute("ALTER TABLE visitas ADD COLUMN status_2a_rodada TEXT DEFAULT 'Planejada'")
    
    if 'sistema_1' in columns_visitas:
        cursor.execute("ALTER TABLE visitas RENAME COLUMN sistema_1 TO equipe_1")
    if 'sistema_2' in columns_visitas:
        cursor.execute("ALTER TABLE visitas RENAME COLUMN sistema_2 TO equipe_2")
    if 'sistema_3' in columns_visitas:
        cursor.execute("ALTER TABLE visitas RENAME COLUMN sistema_3 TO equipe_3")
    if 'sistema_4' in columns_visitas:
        cursor.execute("ALTER TABLE visitas RENAME COLUMN sistema_4 TO equipe_4")

    # Migração da tabela pendencias
    cursor.execute("PRAGMA table_info(pendencias)")
    columns_pendencias = [col[1] for col in cursor.fetchall()]

    if 'cliente' not in columns_pendencias:
        cursor.execute("ALTER TABLE pendencias ADD COLUMN cliente TEXT")
    if 'data_prioridade' not in columns_pendencias:
        cursor.execute("ALTER TABLE pendencias ADD COLUMN data_prioridade TEXT")
    if 'orgao' in columns_pendencias:
        cursor.execute("ALTER TABLE pendencias RENAME COLUMN orgao TO cliente_temp")
        cursor.execute("UPDATE pendencias SET cliente = cliente_temp")
        cursor.execute("ALTER TABLE pendencias DROP COLUMN cliente_temp")
    if 'municipio' in columns_pendencias:
        cursor.execute("ALTER TABLE pendencias DROP COLUMN municipio")
    if 'prioridade' in columns_pendencias:
        cursor.execute("ALTER TABLE pendencias RENAME COLUMN prioridade TO data_prioridade_temp")
        cursor.execute("UPDATE pendencias SET data_prioridade = data_prioridade_temp")
        cursor.execute("ALTER TABLE pendencias DROP COLUMN data_prioridade_temp")
    
    conn.commit()
    conn.close()

# Conectando ao banco de dados
def get_db_connection():
    conn = sqlite3.connect('/tmp/database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicializa o banco de dados antes da primeira requisição
@app.before_request
def before_request_func():
    if not os.path.exists('/tmp/database.db'):
        init_db()

@app.route('/')
def index():
    return render_template('index.html')

# === Rotas para Técnicos ===
@app.route('/tecnicos')
def tecnicos():
    conn = get_db_connection()
    tecnicos_data = conn.execute('SELECT * FROM tecnicos').fetchall()
    equipes_data = conn.execute('SELECT nome FROM equipes').fetchall()
    conn.close()
    return render_template('tecnicos.html', tecnicos=tecnicos_data, equipes=equipes_data)

@app.route('/new_tecnico', methods=['GET', 'POST'])
def new_tecnico():
    conn = get_db_connection()
    equipes_data = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
    conn.close()
    if request.method == 'POST':
        conn = get_db_connection()
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
    return render_template('new_tecnico.html', equipes=equipes_data)

@app.route('/edit_tecnico/<int:id>', methods=['GET', 'POST'])
def edit_tecnico(id):
    conn = get_db_connection()
    tecnico = conn.execute('SELECT * FROM tecnicos WHERE id = ?', (id,)).fetchone()
    equipes_data = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
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
    return render_template('edit_tecnico.html', tecnico=tecnico, equipes=equipes_data)

@app.route('/delete_tecnico/<int:id>', methods=['POST'])
def delete_tecnico(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tecnicos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('tecnicos'))

# === Rotas para Clientes ===
@app.route('/clientes')
def clientes():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT * FROM clientes').fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes_data)

@app.route('/new_cliente', methods=['GET', 'POST'])
def new_cliente():
    conn = get_db_connection()
    sistemas_para_selecao = [row['sigla'] for row in conn.execute('SELECT sigla FROM sistemas').fetchall()]
    conn.close()
    if request.method == 'POST':
        conn = get_db_connection()
        municipio = request.form['municipio']
        orgao = request.form['orgao']
        contrato = request.form['contrato']
        sistemas_list = request.form.getlist('sistemas')
        sistemas_str = ', '.join(sistemas_list)
        conn.execute('INSERT INTO clientes (municipio, orgao, contrato, sistemas) VALUES (?, ?, ?, ?)',
                     (municipio, orgao, contrato, sistemas_str))
        conn.commit()
        conn.close()
        return redirect(url_for('clientes'))
    return render_template('new_cliente.html', sistemas_para_selecao=sistemas_para_selecao)

@app.route('/edit_cliente/<int:id>', methods=['GET', 'POST'])
def edit_cliente(id):
    conn = get_db_connection()
    sistemas_para_selecao = [row['sigla'] for row in conn.execute('SELECT sigla FROM sistemas').fetchall()]
    cliente = conn.execute('SELECT * FROM clientes WHERE id = ?', (id,)).fetchone()
    sistemas_salvos = cliente['sistemas'].split(', ') if cliente['sistemas'] else []
    if request.method == 'POST':
        municipio = request.form['municipio']
        orgao = request.form['orgao']
        contrato = request.form['contrato']
        sistemas_list = request.form.getlist('sistemas')
        sistemas_str = ', '.join(sistemas_list)
        conn.execute('UPDATE clientes SET municipio = ?, orgao = ?, contrato = ?, sistemas = ? WHERE id = ?',
                     (municipio, orgao, contrato, sistemas_str, id))
        conn.commit()
        conn.close()
        return redirect(url_for('clientes'))
    conn.close()
    return render_template('edit_cliente.html', cliente=cliente, sistemas_salvos=sistemas_salvos, sistemas_para_selecao=sistemas_para_selecao)

@app.route('/delete_cliente/<int:id>', methods=['POST'])
def delete_cliente(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM clientes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('clientes'))

# === Rotas para Equipes ===
@app.route('/equipes')
def equipes():
    conn = get_db_connection()
    equipes_data = conn.execute('SELECT * FROM equipes').fetchall()
    tecnicos_data = conn.execute('SELECT nome, contrato FROM tecnicos').fetchall()
    conn.close()
    return render_template('equipes.html', equipes=equipes_data, tecnicos=tecnicos_data)

@app.route('/new_equipe', methods=['GET', 'POST'])
def new_equipe():
    conn = get_db_connection()
    tecnicos_data = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos').fetchall()]
    conn.close()
    if request.method == 'POST':
        conn = get_db_connection()
        nome = request.form['nome']
        sigla = request.form['sigla']
        lider = request.form['lider']
        conn.execute('INSERT INTO equipes (nome, sigla, lider) VALUES (?, ?, ?)',
                     (nome, sigla, lider))
        conn.commit()
        conn.close()
        return redirect(url_for('equipes'))
    return render_template('new_equipe.html', tecnicos=tecnicos_data)

@app.route('/edit_equipe/<int:id>', methods=['GET', 'POST'])
def edit_equipe(id):
    conn = get_db_connection()
    equipe = conn.execute('SELECT * FROM equipes WHERE id = ?', (id,)).fetchone()
    tecnicos_data = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos').fetchall()]
    if request.method == 'POST':
        nome = request.form['nome']
        sigla = request.form['sigla']
        lider = request.form['lider']
        conn.execute('UPDATE equipes SET nome = ?, sigla = ?, lider = ? WHERE id = ?',
                     (nome, sigla, lider, id))
        conn.commit()
        conn.close()
        return redirect(url_for('equipes'))
    conn.close()
    return render_template('edit_equipe.html', equipe=equipe, tecnicos=tecnicos_data)

@app.route('/delete_equipe/<int:id>', methods=['POST'])
def delete_equipe(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM equipes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('equipes'))

# === Rotas para Cronograma ===
@app.route('/cronograma')
def cronograma():
    conn = get_db_connection()
    cronogramas_data = conn.execute('SELECT * FROM cronogramas').fetchall()
    equipes_data = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
    tecnicos_data = [(row['nome'], row['funcao']) for row in conn.execute('SELECT nome, funcao FROM tecnicos').fetchall()]
    conn.close()
    return render_template('cronograma.html', cronogramas=cronogramas_data, equipes=equipes_data, tecnicos=tecnicos_data)

@app.route('/new_cronograma', methods=['GET', 'POST'])
def new_cronograma():
    conn = get_db_connection()
    equipes_data = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
    tecnicos_data = [(row['nome'], row['funcao']) for row in conn.execute('SELECT nome, funcao FROM tecnicos').fetchall()]
    conn.close()
    if request.method == 'POST':
        conn = get_db_connection()
        equipe = request.form['equipe']
        tecnico_nome = request.form['tecnico_nome']
        tecnico_funcao = request.form['tecnico_funcao']
        atividade_domingo = request.form.get('atividade_domingo', '')
        atividade_segunda = request.form.get('atividade_segunda', '')
        atividade_terca = request.form.get('atividade_terca', '')
        atividade_quarta = request.form.get('atividade_quarta', '')
        atividade_quinta = request.form.get('atividade_quinta', '')
        atividade_sexta = request.form.get('atividade_sexta', '')
        atividade_sabado = request.form.get('atividade_sabado', '')
        conn.execute('INSERT INTO cronogramas (equipe, tecnico_nome, tecnico_funcao, atividade_domingo, atividade_segunda, atividade_terca, atividade_quarta, atividade_quinta, atividade_sexta, atividade_sabado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (equipe, tecnico_nome, tecnico_funcao, atividade_domingo, atividade_segunda, atividade_terca, atividade_quarta, atividade_quinta, atividade_sexta, atividade_sabado))
        conn.commit()
        conn.close()
        return redirect(url_for('cronograma'))
    return render_template('new_cronograma.html', equipes=equipes_data, tecnicos=tecnicos_data)

@app.route('/edit_cronograma/<int:id>', methods=['GET', 'POST'])
def edit_cronograma(id):
    conn = get_db_connection()
    cronograma_item = conn.execute('SELECT * FROM cronogramas WHERE id = ?', (id,)).fetchone()
    equipes_data = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
    tecnicos_data = [(row['nome'], row['funcao']) for row in conn.execute('SELECT nome, funcao FROM tecnicos').fetchall()]
    if request.method == 'POST':
        equipe = request.form['equipe']
        tecnico_nome = request.form['tecnico_nome']
        tecnico_funcao = request.form['tecnico_funcao']
        atividade_domingo = request.form.get('atividade_domingo', '')
        atividade_segunda = request.form.get('atividade_segunda', '')
        atividade_terca = request.form.get('atividade_terca', '')
        atividade_quarta = request.form.get('atividade_quarta', '')
        atividade_quinta = request.form.get('atividade_quinta', '')
        atividade_sexta = request.form.get('atividade_sexta', '')
        atividade_sabado = request.form.get('atividade_sabado', '')
        conn.execute('UPDATE cronogramas SET equipe = ?, tecnico_nome = ?, tecnico_funcao = ?, atividade_domingo = ?, atividade_segunda = ?, atividade_terca = ?, atividade_quarta = ?, atividade_quinta = ?, atividade_sexta = ?, atividade_sabado = ? WHERE id = ?',
                     (equipe, tecnico_nome, tecnico_funcao, atividade_domingo, atividade_segunda, atividade_terca, atividade_quarta, atividade_quinta, atividade_sexta, atividade_sabado, id))
        conn.commit()
        conn.close()
        return redirect(url_for('cronograma'))
    conn.close()
    return render_template('edit_cronograma.html', cronograma_item=cronograma_item, equipes=equipes_data, tecnicos=tecnicos_data)

@app.route('/delete_cronograma/<int:id>', methods=['POST'])
def delete_cronograma(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM cronogramas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('cronograma'))

# === Rotas para Visitas ===
@app.route('/visitas')
def visitas():
    conn = get_db_connection()
    visitas_data = conn.execute('SELECT id, localidade_orgao, data_1a_rodada, equipe_1, tecnico_1, equipe_2, tecnico_2, data_2a_rodada, equipe_3, tecnico_3, equipe_4, tecnico_4, status_1a_rodada, status_2a_rodada FROM visitas').fetchall()
    clientes_data = [f"{row['municipio']} - {row['orgao']}" for row in conn.execute('SELECT municipio, orgao FROM clientes').fetchall()]
    tecnicos_data = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos').fetchall()]
    equipes_data = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
    conn.close()
    return render_template('visitas.html', visitas=visitas_data, clientes=clientes_data, tecnicos=tecnicos_data, equipes=equipes_data)

@app.route('/new_visita', methods=['GET', 'POST'])
def new_visita():
    conn = get_db_connection()
    clientes_data = [f"{row['municipio']} - {row['orgao']}" for row in conn.execute('SELECT municipio, orgao FROM clientes').fetchall()]
    tecnicos_data = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos').fetchall()]
    equipes_data = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
    conn.close()
    if request.method == 'POST':
        conn = get_db_connection()
        localidade_orgao = request.form['localidade_orgao']
        status_1a_rodada = request.form['status_1a_rodada']
        data_1a_rodada = request.form['data_1a_rodada']
        equipe_1 = request.form['equipe_1']
        tecnico_1 = request.form['tecnico_1']
        equipe_2 = request.form['equipe_2']
        tecnico_2 = request.form['tecnico_2']
        status_2a_rodada = request.form['status_2a_rodada']
        data_2a_rodada = request.form['data_2a_rodada']
        equipe_3 = request.form['equipe_3']
        tecnico_3 = request.form['tecnico_3']
        equipe_4 = request.form['equipe_4']
        tecnico_4 = request.form['tecnico_4']
        conn.execute('INSERT INTO visitas (localidade_orgao, status_1a_rodada, data_1a_rodada, equipe_1, tecnico_1, equipe_2, tecnico_2, status_2a_rodada, data_2a_rodada, equipe_3, tecnico_3, equipe_4, tecnico_4) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (localidade_orgao, status_1a_rodada, data_1a_rodada, equipe_1, tecnico_1, equipe_2, tecnico_2, status_2a_rodada, data_2a_rodada, equipe_3, tecnico_3, equipe_4, tecnico_4))
        conn.commit()
        conn.close()
        return redirect(url_for('visitas'))
    return render_template('new_visita.html', clientes=clientes_data, tecnicos=tecnicos_data, equipes=equipes_data)

@app.route('/edit_visita/<int:id>', methods=['GET', 'POST'])
def edit_visita(id):
    conn = get_db_connection()
    visita = conn.execute('SELECT * FROM visitas WHERE id = ?', (id,)).fetchone()
    clientes_data = [f"{row['municipio']} - {row['orgao']}" for row in conn.execute('SELECT municipio, orgao FROM clientes').fetchall()]
    tecnicos_data = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos').fetchall()]
    equipes_data = [row['nome'] for row in conn.execute('SELECT nome FROM equipes').fetchall()]
    if request.method == 'POST':
        localidade_orgao = request.form['localidade_orgao']
        status_1a_rodada = request.form['status_1a_rodada']
        data_1a_rodada = request.form['data_1a_rodada']
        equipe_1 = request.form['equipe_1']
        tecnico_1 = request.form['tecnico_1']
        equipe_2 = request.form['equipe_2']
        tecnico_2 = request.form['tecnico_2']
        status_2a_rodada = request.form['status_2a_rodada']
        data_2a_rodada = request.form['data_2a_rodada']
        equipe_3 = request.form['equipe_3']
        tecnico_3 = request.form['tecnico_3']
        equipe_4 = request.form['equipe_4']
        tecnico_4 = request.form['tecnico_4']
        conn.execute('UPDATE visitas SET localidade_orgao = ?, status_1a_rodada = ?, data_1a_rodada = ?, equipe_1 = ?, tecnico_1 = ?, equipe_2 = ?, tecnico_2 = ?, status_2a_rodada = ?, data_2a_rodada = ?, equipe_3 = ?, tecnico_3 = ?, equipe_4 = ?, tecnico_4 = ? WHERE id = ?',
                     (localidade_orgao, status_1a_rodada, data_1a_rodada, equipe_1, tecnico_1, equipe_2, tecnico_2, status_2a_rodada, data_2a_rodada, equipe_3, tecnico_3, equipe_4, tecnico_4, id))
        conn.commit()
        conn.close()
        return redirect(url_for('visitas'))
    conn.close()
    return render_template('edit_visita.html', visita=visita, clientes=clientes_data, tecnicos=tecnicos_data, equipes=equipes_data)

@app.route('/delete_visita/<int:id>', methods=['POST'])
def delete_visita(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM visitas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('visitas'))

# === Rotas para Pendências ===
@app.route('/pendencias')
def pendencias():
    conn = get_db_connection()
    pendencias_data = conn.execute('SELECT id, processo, cliente, sistema, data_prioridade, prazo_entrega, status FROM pendencias').fetchall()
    sistemas_para_selecao = [row['sigla'] for row in conn.execute('SELECT sigla FROM sistemas').fetchall()]
    clientes_data = [f"{row['municipio']} - {row['orgao']}" for row in conn.execute('SELECT municipio, orgao FROM clientes').fetchall()]
    conn.close()
    return render_template('pendencias.html', pendencias=pendencias_data, sistemas_para_selecao=sistemas_para_selecao, clientes=clientes_data)

@app.route('/new_pendencia', methods=['GET', 'POST'])
def new_pendencia():
    conn = get_db_connection()
    sistemas_para_selecao = [row['sigla'] for row in conn.execute('SELECT sigla FROM sistemas').fetchall()]
    clientes_data = [f"{row['municipio']} - {row['orgao']}" for row in conn.execute('SELECT municipio, orgao FROM clientes').fetchall()]
    conn.close()
    if request.method == 'POST':
        conn = get_db_connection()
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
    return render_template('new_pendencia.html', sistemas_para_selecao=sistemas_para_selecao, clientes=clientes_data)

@app.route('/edit_pendencia/<int:id>', methods=['GET', 'POST'])
def edit_pendencia(id):
    conn = get_db_connection()
    pendencia = conn.execute('SELECT * FROM pendencias WHERE id = ?', (id,)).fetchone()
    sistemas_para_selecao = [row['sigla'] for row in conn.execute('SELECT sigla FROM sistemas').fetchall()]
    clientes_data = [f"{row['municipio']} - {row['orgao']}" for row in conn.execute('SELECT municipio, orgao FROM clientes').fetchall()]
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
    return render_template('edit_pendencia.html', pendencia=pendencia, sistemas_para_selecao=sistemas_para_selecao, clientes=clientes_data)

@app.route('/delete_pendencia/<int:id>', methods=['POST'])
def delete_pendencia(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM pendencias WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('pendencias'))

# === Rotas para Férias ===
@app.route('/ferias')
def ferias():
    conn = get_db_connection()
    ferias_data = conn.execute('SELECT * FROM ferias').fetchall()
    tecnicos_data = conn.execute('SELECT nome, contrato FROM tecnicos').fetchall()
    conn.close()
    return render_template('ferias.html', ferias=ferias_data, tecnicos=tecnicos_data)

@app.route('/new_ferias', methods=['GET', 'POST'])
def new_ferias():
    conn = get_db_connection()
    tecnicos_data = conn.execute('SELECT nome, contrato FROM tecnicos').fetchall()
    conn.close()
    if request.method == 'POST':
        conn = get_db_connection()
        funcionario = request.form['funcionario']
        admissao = request.form['admissao']
        contrato = request.form['contrato']
        ano = request.form['ano']
        data_inicio = request.form.get('data_inicio')
        data_termino = request.form.get('data_termino')
        obs = request.form['obs']
        conn.execute('INSERT INTO ferias (funcionario, admissao, contrato, ano, data_inicio, data_termino, obs) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (funcionario, admissao, contrato, ano, data_inicio, data_termino, obs))
        conn.commit()
        conn.close()
        return redirect(url_for('ferias'))
    return render_template('new_ferias.html', tecnicos=tecnicos_data)

@app.route('/edit_ferias/<int:id>', methods=['GET', 'POST'])
def edit_ferias(id):
    conn = get_db_connection()
    ferias_item = conn.execute('SELECT * FROM ferias WHERE id = ?', (id,)).fetchone()
    tecnicos_data = conn.execute('SELECT nome, contrato FROM tecnicos').fetchall()
    if request.method == 'POST':
        funcionario = request.form['funcionario']
        admissao = request.form['admissao']
        contrato = request.form['contrato']
        ano = request.form['ano']
        data_inicio = request.form.get('data_inicio')
        data_termino = request.form.get('data_termino')
        obs = request.form['obs']
        conn.execute('UPDATE ferias SET funcionario = ?, admissao = ?, contrato = ?, ano = ?, data_inicio = ?, data_termino = ?, obs = ? WHERE id = ?',
                     (funcionario, admissao, contrato, ano, data_inicio, data_termino, obs, id))
        conn.commit()
        conn.close()
        return redirect(url_for('ferias'))
    conn.close()
    return render_template('edit_ferias.html', ferias_item=ferias_item, tecnicos=tecnicos_data)

@app.route('/delete_ferias/<int:id>', methods=['POST'])
def delete_ferias(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM ferias WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('ferias'))

# === Rotas para Sistemas ===
@app.route('/sistemas')
def sistemas():
    conn = get_db_connection()
    sistemas_data = conn.execute('SELECT * FROM sistemas').fetchall()
    conn.close()
    return render_template('sistemas.html', sistemas=sistemas_data)

@app.route('/new_sistema', methods=['GET', 'POST'])
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
def delete_sistema(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM sistemas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('sistemas'))

if __name__ == '__main__':
    app.run(debug=True)