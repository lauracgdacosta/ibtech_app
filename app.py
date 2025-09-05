import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import datetime

app = Flask(__name__)

# Configurações da Aplicação
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
    """Formata uma string de data AAAA-MM-DD para DD/MM/AAAA."""
    if value is None or value == "":
        return ""
    try:
        date_obj = datetime.datetime.strptime(value, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except ValueError:
        try:
            date_obj = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return date_obj.strftime('%d/%m/%Y %H:%M')
        except ValueError:
            return value

app.jinja_env.filters['dateformat'] = format_date

# --- Configuração do Banco de Dados ---
def init_db():
    conn = sqlite3.connect('/tmp/database.db')
    cursor = conn.cursor()
    
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prestacao_contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            sistema TEXT,
            responsavel TEXT,
            modulo TEXT,
            periodo TEXT,
            competencia TEXT,
            status TEXT,
            observacao TEXT,
            atualizado_por TEXT
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS cronogramas')
    cursor.execute('DROP TABLE IF EXISTS tarefas')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cliente TEXT,
            data_inicio_previsto DATE,
            data_termino_previsto DATE,
            status TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            atividade_id TEXT,
            descricao TEXT NOT NULL,
            data_inicio DATE,
            data_termino DATE,
            responsavel_pm TEXT,
            responsavel_cm TEXT,
            status TEXT NOT NULL,
            local_execucao TEXT,
            observacoes TEXT,
            FOREIGN KEY (projeto_id) REFERENCES projetos (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('/tmp/database.db')
    conn.row_factory = sqlite3.Row
    return conn

with app.app_context():
    init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

@app.route('/cadastros')
@login_required
def cadastros():
    return render_template('cadastros.html')

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

@app.route('/projetos')
@login_required
def projetos():
    conn = get_db_connection()
    lista_projetos = conn.execute('SELECT * FROM projetos ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('projetos.html', projetos=lista_projetos)

@app.route('/new_projeto', methods=['GET', 'POST'])
@login_required
def new_projeto():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    if request.method == 'POST':
        nome = request.form['nome']
        cliente = request.form['cliente']
        data_inicio = request.form['data_inicio_previsto']
        data_termino = request.form['data_termino_previsto']
        status = request.form['status']
        cursor = conn.cursor()
        cursor.execute('INSERT INTO projetos (nome, cliente, data_inicio_previsto, data_termino_previsto, status) VALUES (?, ?, ?, ?, ?)',
                     (nome, cliente, data_inicio, data_termino, status))
        novo_projeto_id = cursor.lastrowid
        for tarefa in TAREFAS_PADRAO:
            cursor.execute('INSERT INTO tarefas (projeto_id, atividade_id, descricao, tipo, status) VALUES (?, ?, ?, ?, ?)',
                         (novo_projeto_id, tarefa['id'], tarefa['desc'], tarefa['tipo'], 'Planejada'))
        conn.commit()
        conn.close()
        flash('Projeto criado com sucesso e checklist padrão adicionado!', 'success')
        return redirect(url_for('projetos'))
    conn.close()
    return render_template('new_projeto.html', clientes=clientes)

@app.route('/projeto/edit/<int:projeto_id>', methods=['GET', 'POST'])
@login_required
def edit_projeto(projeto_id):
    conn = get_db_connection()
    projeto = conn.execute('SELECT * FROM projetos WHERE id = ?', (projeto_id,)).fetchone()
    if request.method == 'POST':
        nome = request.form['nome']
        cliente = request.form['cliente']
        data_inicio = request.form['data_inicio_previsto']
        data_termino = request.form['data_termino_previsto']
        status = request.form['status']
        conn.execute('UPDATE projetos SET nome = ?, cliente = ?, data_inicio_previsto = ?, data_termino_previsto = ?, status = ? WHERE id = ?',
                     (nome, cliente, data_inicio, data_termino, status, projeto_id))
        conn.commit()
        conn.close()
        flash('Projeto atualizado com sucesso!', 'success')
        return redirect(url_for('projetos'))
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    conn.close()
    return render_template('edit_projeto.html', projeto=projeto, clientes=clientes)

@app.route('/projeto/delete/<int:projeto_id>', methods=['POST'])
@login_required
def delete_projeto(projeto_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM projetos WHERE id = ?', (projeto_id,))
    conn.commit()
    conn.close()
    flash('Projeto e todas as suas tarefas foram excluídos com sucesso!', 'success')
    return redirect(url_for('projetos'))

@app.route('/projeto/<int:projeto_id>')
@login_required
def checklist_projeto(projeto_id):
    conn = get_db_connection()
    projeto = conn.execute('SELECT * FROM projetos WHERE id = ?', (projeto_id,)).fetchone()
    tarefas_from_db = conn.execute('SELECT * FROM tarefas WHERE projeto_id = ? ORDER BY atividade_id', (projeto_id,)).fetchall()
    conn.close()
    if projeto is None:
        flash('Projeto não encontrado.', 'danger')
        return redirect(url_for('projetos'))
    lista_tarefas_com_duracao = []
    for tarefa in tarefas_from_db:
        tarefa_dict = dict(tarefa)
        duracao = ""
        if tarefa_dict['data_inicio'] and tarefa_dict['data_termino']:
            try:
                data_inicio = datetime.datetime.strptime(tarefa_dict['data_inicio'], '%Y-%m-%d')
                data_termino = datetime.datetime.strptime(tarefa_dict['data_termino'], '%Y-%m-%d')
                delta = (data_termino - data_inicio).days + 1
                duracao = f"{delta} d" if delta >= 0 else ""
            except (ValueError, TypeError):
                duracao = ""
        tarefa_dict['duracao_calculada'] = duracao
        lista_tarefas_com_duracao.append(tarefa_dict)
    return render_template('checklist_projeto.html', projeto=projeto, tarefas=lista_tarefas_com_duracao)

@app.route('/projeto/<int:projeto_id>/new_tarefa', methods=['POST'])
@login_required
def new_tarefa(projeto_id):
    atividade_id = request.form['atividade_id']
    descricao = request.form['descricao']
    data_inicio = request.form['data_inicio'] or None
    data_termino = request.form['data_termino'] or None
    responsavel_pm = request.form['responsavel_pm']
    responsavel_cm = request.form['responsavel_cm']
    local_execucao = request.form['local_execucao']
    observacoes = request.form['observacoes']
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO tarefas (projeto_id, atividade_id, descricao, data_inicio, data_termino, responsavel_pm, responsavel_cm, status, local_execucao, observacoes, tipo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (projeto_id, atividade_id, descricao, data_inicio, data_termino, responsavel_pm, responsavel_cm, 'Planejada', local_execucao, observacoes, 'tarefa'))
    conn.commit()
    conn.close()
    flash('Tarefa adicionada com sucesso!', 'success')
    return redirect(url_for('checklist_projeto', projeto_id=projeto_id))

@app.route('/tarefa/edit/<int:tarefa_id>', methods=['GET', 'POST'])
@login_required
def edit_tarefa(tarefa_id):
    conn = get_db_connection()
    tarefa = conn.execute('SELECT * FROM tarefas WHERE id = ?', (tarefa_id,)).fetchone()
    if request.method == 'POST':
        atividade_id = request.form['atividade_id']
        descricao = request.form['descricao']
        data_inicio = request.form['data_inicio'] or None
        data_termino = request.form['data_termino'] or None
        responsavel_pm = request.form['responsavel_pm']
        responsavel_cm = request.form['responsavel_cm']
        status = request.form['status']
        local_execucao = request.form['local_execucao']
        observacoes = request.form['observacoes']
        conn.execute('''
            UPDATE tarefas SET
            atividade_id = ?, descricao = ?, data_inicio = ?, data_termino = ?, 
            responsavel_pm = ?, responsavel_cm = ?, status = ?, local_execucao = ?, observacoes = ?
            WHERE id = ?
        ''', (atividade_id, descricao, data_inicio, data_termino, responsavel_pm, responsavel_cm, status, local_execucao, observacoes, tarefa_id))
        conn.commit()
        conn.close()
        flash('Tarefa atualizada com sucesso!', 'success')
        return redirect(url_for('checklist_projeto', projeto_id=tarefa['projeto_id']))
    tecnicos = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    locais = sorted(list(set([f"{c['municipio']} - {c['orgao']}" for c in clientes_data] + ['Ibtech'])))
    conn.close()
    return render_template('edit_tarefa.html', tarefa=tarefa, tecnicos=tecnicos, locais=locais)

@app.route('/tarefa/toggle_status/<int:tarefa_id>', methods=['POST'])
@login_required
def toggle_tarefa_status(tarefa_id):
    conn = get_db_connection()
    tarefa = conn.execute('SELECT * FROM tarefas WHERE id = ?', (tarefa_id,)).fetchone()
    if tarefa:
        novo_status = 'Concluída' if tarefa['status'] != 'Concluída' else 'Planejada'
        conn.execute('UPDATE tarefas SET status = ? WHERE id = ?', (novo_status, tarefa_id))
        conn.commit()
        flash(f'Status da tarefa alterado para "{novo_status}"!', 'success')
    projeto_id = tarefa['projeto_id'] if tarefa else None
    conn.close()
    if projeto_id:
        return redirect(url_for('checklist_projeto', projeto_id=projeto_id))
    return redirect(url_for('projetos'))

@app.route('/tarefa/delete/<int:tarefa_id>', methods=['POST'])
@login_required
def delete_tarefa(tarefa_id):
    conn = get_db_connection()
    tarefa = conn.execute('SELECT projeto_id FROM tarefas WHERE id = ?', (tarefa_id,)).fetchone()
    projeto_id = tarefa['projeto_id'] if tarefa else None
    conn.execute('DELETE FROM tarefas WHERE id = ?', (tarefa_id,))
    conn.commit()
    conn.close()
    flash('Tarefa excluída com sucesso.', 'success')
    if projeto_id:
        return redirect(url_for('checklist_projeto', projeto_id=projeto_id))
    return redirect(url_for('projetos'))

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
    # ... (código da rota)
    return render_template('new_pendencia.html', clientes=clientes, sistemas_para_selecao=sistemas_para_selecao)

@app.route('/edit_pendencia/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_pendencia(id):
    # ... (código da rota)
    return render_template('edit_pendencia.html', pendencia=pendencia, clientes=clientes, sistemas_para_selecao=sistemas_para_selecao)

@app.route('/delete_pendencia/<int:id>', methods=['POST'])
@login_required
def delete_pendencia(id):
    # ... (código da rota)
    return redirect(url_for('pendencias'))

@app.route('/ferias')
@login_required
def ferias():
    # ... (código da rota)
    return render_template('ferias.html', ferias=ferias_data)

# ... (todas as outras rotas de ferias, agenda, prestacao_contas, usuarios e autenticação)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)