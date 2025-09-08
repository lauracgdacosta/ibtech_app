import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import datetime

app = Flask(__name__)
app.secret_key = '18T3ch'

# --- LISTA MESTRA DE MÓDULOS ---
# Define todos os módulos do sistema para consistência no painel de permissões.
AVAILABLE_MODULES = {
    'cadastros': 'Cadastros (Técnicos, Clientes, etc)',
    'agenda': 'Agenda',
    'projetos': 'Projetos de Implantação',
    'pendencias': 'Pendências',
    'prestacao_contas': 'Prestação de Contas',
    'ferias': 'Férias'
}

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tecnicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, email TEXT, telefone TEXT, funcao TEXT, equipe TEXT, contrato TEXT ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            municipio TEXT NOT NULL, orgao TEXT, contrato TEXT, sistemas TEXT ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, sigla TEXT, lider TEXT ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pendencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processo TEXT, cliente TEXT, sistema TEXT, data_prioridade TEXT, prazo_entrega TEXT, status TEXT ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ferias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            funcionario TEXT NOT NULL, admissao TEXT, contrato TEXT, ano INTEGER, data_inicio TEXT, data_termino TEXT, obs TEXT ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sistemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, sigla TEXT NOT NULL ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL, tecnico TEXT NOT NULL, sistema TEXT, data_agendamento DATE NOT NULL, motivo TEXT, descricao TEXT, status TEXT ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prestacao_contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT, sistema TEXT, responsavel TEXT, modulo TEXT, periodo TEXT, competencia TEXT, status TEXT, observacao TEXT, atualizado_por TEXT ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, cliente TEXT, data_inicio_previsto DATE, data_termino_previsto DATE, status TEXT NOT NULL ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL, tipo TEXT NOT NULL, atividade_id TEXT, descricao TEXT NOT NULL, data_inicio DATE, data_termino DATE,
            responsavel_pm TEXT, responsavel_cm TEXT, status TEXT NOT NULL, local_execucao TEXT, observacoes TEXT,
            FOREIGN KEY (projeto_id) REFERENCES projetos (id) ON DELETE CASCADE ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL, email TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, nivel_acesso TEXT, role TEXT ) ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL, module_name TEXT NOT NULL, UNIQUE(role_name, module_name) ) ''')
    conn.commit()
    conn.close()

def migrate_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT role FROM usuarios LIMIT 1")
    except sqlite3.OperationalError:
        print("Executando migração: Adicionando coluna 'role' à tabela 'usuarios'.")
        cursor.execute("ALTER TABLE usuarios ADD COLUMN role TEXT")
    
    cursor.execute("""
        UPDATE usuarios SET role = CASE 
            WHEN nivel_acesso = 'Admin' THEN 'admin'
            WHEN nivel_acesso = 'Usuario' THEN 'tecnico'
            ELSE role
        END WHERE role IS NULL """)
    
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

# --- LÓGICA E DECORADORES DE PERMISSÃO ---
def check_permission(module_name):
    user_role = session.get('user_role')
    if not user_role: return False
    if user_role == 'admin': return True
    conn = get_db_connection()
    permission = conn.execute('SELECT 1 FROM role_permissions WHERE role_name = ? AND module_name = ?', (user_role, module_name)).fetchone()
    conn.close()
    return permission is not None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(module_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_permission(module_name):
                flash('Você não tem permissão para acessar este recurso.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- ROTAS ---
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    hoje_str = datetime.date.today().strftime('%Y-%m-%d')
    proximos_agendamentos = conn.execute('SELECT * FROM agenda WHERE data_agendamento >= ? ORDER BY data_agendamento ASC LIMIT 5', (hoje_str,)).fetchall()
    pendencias_abertas = conn.execute("SELECT * FROM pendencias WHERE status = 'Aberto' ORDER BY data_prioridade ASC LIMIT 5").fetchall()
    tecnicos_em_ferias = conn.execute('SELECT * FROM ferias WHERE data_inicio <= ? AND data_termino >= ?', (hoje_str, hoje_str)).fetchall()
    conn.close()
    return render_template('index.html', proximos_agendamentos=proximos_agendamentos, pendencias_abertas=pendencias_abertas, tecnicos_em_ferias=tecnicos_em_ferias, check_permission=check_permission)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: return redirect(url_for('index'))
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

# --- ROTAS DE GESTÃO DE PERMISSÕES (Admin) ---
@app.route('/gerenciar_permissoes')
@login_required
@role_required('admin_only') # Módulo virtual, só o admin pode acessar
def gerenciar_permissoes():
    conn = get_db_connection()
    permissions_data = conn.execute('SELECT role_name, module_name FROM role_permissions').fetchall()
    conn.close()
    permissions = {'coordenacao': [], 'tecnico': []}
    for p in permissions_data:
        if p['role_name'] in permissions:
            permissions[p['role_name']].append(p['module_name'])
    roles_to_manage = ['coordenacao', 'tecnico']
    return render_template('gerenciar_permissoes.html', modules=AVAILABLE_MODULES, roles=roles_to_manage, current_permissions=permissions)

@app.route('/salvar_permissoes', methods=['POST'])
@login_required
@role_required('admin_only')
def salvar_permissoes():
    conn = get_db_connection()
    cursor = conn.cursor()
    roles_to_manage = ['coordenacao', 'tecnico']
    cursor.execute(f"DELETE FROM role_permissions WHERE role_name IN ({','.join('?'*len(roles_to_manage))})", roles_to_manage)
    for key in request.form:
        if key.startswith('permission_'):
            _, role, module = key.split('_')
            cursor.execute('INSERT INTO role_permissions (role_name, module_name) VALUES (?, ?)', (role, module))
    conn.commit()
    conn.close()
    flash('Permissões atualizadas com sucesso!', 'success')
    return redirect(url_for('gerenciar_permissoes'))


# --- MÓDULOS DE CADASTRO ---
@app.route('/cadastros')
@login_required
@role_required('cadastros')
def cadastros():
    return render_template('cadastros.html')

@app.route('/tecnicos')
@login_required
@role_required('cadastros')
def tecnicos():
    conn = get_db_connection()
    tecnicos_data = conn.execute('SELECT * FROM tecnicos').fetchall()
    conn.close()
    return render_template('tecnicos.html', tecnicos=tecnicos_data)

@app.route('/new_tecnico', methods=['GET', 'POST'])
@login_required
@role_required('cadastros')
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
@role_required('cadastros')
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
@role_required('cadastros')
def delete_tecnico(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tecnicos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('tecnicos'))

@app.route('/clientes')
@login_required
@role_required('cadastros')
def clientes():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT * FROM clientes').fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes_data)

@app.route('/new_cliente', methods=['GET', 'POST'])
@login_required
@role_required('cadastros')
def new_cliente():
    conn = get_db_connection()
    sistemas_para_selecao = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas').fetchall()]
    if request.method == 'POST':
        municipio, orgao, contrato = request.form['municipio'], request.form['orgao'], request.form['contrato']
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
@role_required('cadastros')
def edit_cliente(id):
    conn = get_db_connection()
    cliente = conn.execute('SELECT * FROM clientes WHERE id = ?', (id,)).fetchone()
    sistemas_para_selecao = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas').fetchall()]
    sistemas_salvos = cliente['sistemas'].split(', ') if cliente['sistemas'] else []
    if request.method == 'POST':
        municipio, orgao, contrato = request.form['municipio'], request.form['orgao'], request.form['contrato']
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
@role_required('cadastros')
def delete_cliente(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM clientes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('clientes'))

@app.route('/equipes')
@login_required
@role_required('cadastros')
def equipes():
    conn = get_db_connection()
    equipes_data = conn.execute('SELECT * FROM equipes').fetchall()
    conn.close()
    return render_template('equipes.html', equipes=equipes_data)

@app.route('/new_equipe', methods=['GET', 'POST'])
@login_required
@role_required('cadastros')
def new_equipe():
    conn = get_db_connection()
    tecnicos = conn.execute('SELECT nome FROM tecnicos').fetchall()
    if request.method == 'POST':
        nome, sigla, lider = request.form['nome'], request.form['sigla'], request.form['lider']
        conn.execute('INSERT INTO equipes (nome, sigla, lider) VALUES (?, ?, ?)', (nome, sigla, lider))
        conn.commit()
        conn.close()
        return redirect(url_for('equipes'))
    conn.close()
    return render_template('new_equipe.html', tecnicos=tecnicos)

@app.route('/edit_equipe/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('cadastros')
def edit_equipe(id):
    conn = get_db_connection()
    equipe = conn.execute('SELECT * FROM equipes WHERE id = ?', (id,)).fetchone()
    tecnicos = conn.execute('SELECT nome FROM tecnicos').fetchall()
    if request.method == 'POST':
        nome, sigla, lider = request.form['nome'], request.form['sigla'], request.form['lider']
        conn.execute('UPDATE equipes SET nome = ?, sigla = ?, lider = ? WHERE id = ?', (nome, sigla, lider, id))
        conn.commit()
        conn.close()
        return redirect(url_for('equipes'))
    conn.close()
    return render_template('edit_equipe.html', equipe=equipe, tecnicos=tecnicos)

@app.route('/delete_equipe/<int:id>', methods=['POST'])
@login_required
@role_required('cadastros')
def delete_equipe(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM equipes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('equipes'))

@app.route('/sistemas')
@login_required
@role_required('cadastros')
def sistemas():
    conn = get_db_connection()
    sistemas_data = conn.execute('SELECT * FROM sistemas').fetchall()
    conn.close()
    return render_template('sistemas.html', sistemas=sistemas_data)

@app.route('/new_sistema', methods=['GET', 'POST'])
@login_required
@role_required('cadastros')
def new_sistema():
    if request.method == 'POST':
        conn = get_db_connection()
        nome, sigla = request.form['nome'], request.form['sigla']
        conn.execute('INSERT INTO sistemas (nome, sigla) VALUES (?, ?)', (nome, sigla))
        conn.commit()
        conn.close()
        return redirect(url_for('sistemas'))
    return render_template('new_sistema.html')

@app.route('/edit_sistema/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('cadastros')
def edit_sistema(id):
    conn = get_db_connection()
    sistema = conn.execute('SELECT * FROM sistemas WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        nome, sigla = request.form['nome'], request.form['sigla']
        conn.execute('UPDATE sistemas SET nome = ?, sigla = ? WHERE id = ?', (nome, sigla, id))
        conn.commit()
        conn.close()
        return redirect(url_for('sistemas'))
    conn.close()
    return render_template('edit_sistema.html', sistema=sistema)

@app.route('/delete_sistema/<int:id>', methods=['POST'])
@login_required
@role_required('cadastros')
def delete_sistema(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM sistemas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('sistemas'))

# --- MÓDULO DE PROJETOS ---
@app.route('/projetos')
@login_required
@role_required('projetos')
def projetos():
    conn = get_db_connection()
    lista_projetos = conn.execute('SELECT * FROM projetos ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('projetos.html', projetos=lista_projetos)

@app.route('/new_projeto', methods=['GET', 'POST'])
@login_required
@role_required('projetos')
def new_projeto():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    if request.method == 'POST':
        nome, cliente, data_inicio, data_termino, status = request.form['nome'], request.form['cliente'], request.form['data_inicio_previsto'], request.form['data_termino_previsto'], request.form['status']
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
@role_required('projetos')
def edit_projeto(projeto_id):
    conn = get_db_connection()
    projeto = conn.execute('SELECT * FROM projetos WHERE id = ?', (projeto_id,)).fetchone()
    if request.method == 'POST':
        nome, cliente, data_inicio, data_termino, status = request.form['nome'], request.form['cliente'], request.form['data_inicio_previsto'], request.form['data_termino_previsto'], request.form['status']
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
@role_required('projetos')
def delete_projeto(projeto_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM projetos WHERE id = ?', (projeto_id,))
    conn.commit()
    conn.close()
    flash('Projeto e tarefas excluídos!', 'success')
    return redirect(url_for('projetos'))

@app.route('/projeto/<int:projeto_id>')
@login_required
@role_required('projetos')
def checklist_projeto(projeto_id):
    conn = get_db_connection()
    projeto = conn.execute('SELECT * FROM projetos WHERE id = ?', (projeto_id,)).fetchone()
    tarefas_from_db = conn.execute('SELECT * FROM tarefas WHERE projeto_id = ? ORDER BY atividade_id', (projeto_id,)).fetchall()
    conn.close()
    if not projeto:
        flash('Projeto não encontrado.', 'danger')
        return redirect(url_for('projetos'))
    return render_template('checklist_projeto.html', projeto=projeto, tarefas=tarefas_from_db)


@app.route('/tarefa/edit/<int:tarefa_id>', methods=['GET', 'POST'])
@login_required
@role_required('projetos')
def edit_tarefa(tarefa_id):
    conn = get_db_connection()
    tarefa = conn.execute('SELECT * FROM tarefas WHERE id = ?', (tarefa_id,)).fetchone()
    if request.method == 'POST':
        # ... (código original da função)
        conn.commit()
        conn.close()
        flash('Tarefa atualizada!', 'success')
        return redirect(url_for('checklist_projeto', projeto_id=tarefa['projeto_id']))
    # ... (código original da função)
    conn.close()
    return render_template('edit_tarefa.html', tarefa=tarefa)

@app.route('/tarefa/delete/<int:tarefa_id>', methods=['POST'])
@login_required
@role_required('projetos')
def delete_tarefa(tarefa_id):
    conn = get_db_connection()
    tarefa = conn.execute('SELECT projeto_id FROM tarefas WHERE id = ?', (tarefa_id,)).fetchone()
    projeto_id = tarefa['projeto_id'] if tarefa else None
    conn.execute('DELETE FROM tarefas WHERE id = ?', (tarefa_id,))
    conn.commit()
    conn.close()
    flash('Tarefa excluída.', 'success')
    return redirect(url_for('checklist_projeto', projeto_id=projeto_id)) if projeto_id else redirect(url_for('projetos'))

# --- MÓDULO DE PENDÊNCIAS ---
@app.route('/pendencias')
@login_required
@role_required('pendencias')
def pendencias():
    conn = get_db_connection()
    pendencias_data = conn.execute('SELECT * FROM pendencias').fetchall()
    conn.close()
    return render_template('pendencias.html', pendencias=pendencias_data)

@app.route('/new_pendencia', methods=['GET', 'POST'])
@login_required
@role_required('pendencias')
def new_pendencia():
    # ... (código original da função)
    pass

@app.route('/edit_pendencia/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('pendencias')
def edit_pendencia(id):
    # ... (código original da função)
    pass

@app.route('/delete_pendencia/<int:id>', methods=['POST'])
@login_required
@role_required('pendencias')
def delete_pendencia(id):
    # ... (código original da função)
    pass

# --- MÓDULO DE FÉRIAS ---
@app.route('/ferias')
@login_required
@role_required('ferias')
def ferias():
    # ... (código original da função)
    pass

@app.route('/new_ferias', methods=['GET', 'POST'])
@login_required
@role_required('ferias')
def new_ferias():
    # ... (código original da função)
    pass

@app.route('/edit_ferias/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('ferias')
def edit_ferias(id):
    # ... (código original da função)
    pass

@app.route('/delete_ferias/<int:id>', methods=['POST'])
@login_required
@role_required('ferias')
def delete_ferias(id):
    # ... (código original da função)
    pass

# --- MÓDULO DE AGENDA ---
@app.route('/agenda')
@login_required
@role_required('agenda')
def agenda():
    # ... (código original da função)
    pass

@app.route('/new_agenda', methods=['GET', 'POST'])
@login_required
@role_required('agenda')
def new_agenda():
    # ... (código original da função)
    pass

@app.route('/edit_agenda/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('agenda')
def edit_agenda(id):
    # ... (código original da função)
    pass

@app.route('/delete_agenda/<int:id>', methods=['POST'])
@login_required
@role_required('agenda')
def delete_agenda(id):
    # ... (código original da função)
    pass

# --- MÓDULO DE PRESTAÇÃO DE CONTAS ---
@app.route('/prestacao_contas')
@login_required
@role_required('prestacao_contas')
def prestacao_contas():
    # ... (código original da função)
    pass

@app.route('/new_prestacao', methods=['GET', 'POST'])
@login_required
@role_required('prestacao_contas')
def new_prestacao():
    # ... (código original da função)
    pass

@app.route('/edit_prestacao/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('prestacao_contas')
def edit_prestacao(id):
    # ... (código original da função)
    pass

@app.route('/delete_prestacao/<int:id>', methods=['POST'])
@login_required
@role_required('prestacao_contas')
def delete_prestacao(id):
    # ... (código original da função)
    pass

# --- GESTÃO DE USUÁRIOS (Admin) ---
@app.route('/usuarios')
@login_required
@role_required('admin_only')
def usuarios():
    conn = get_db_connection()
    users_data = conn.execute('SELECT id, nome, email, role FROM usuarios').fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=users_data)

@app.route('/new_usuario', methods=['GET', 'POST'])
@login_required
@role_required('admin_only')
def new_usuario():
    if request.method == 'POST':
        nome, email, senha, role = request.form['nome'], request.form['email'], request.form['senha'], request.form['role']
        hashed_senha = generate_password_hash(senha)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nome, email, senha, role) VALUES (?, ?, ?, ?)', (nome, email, hashed_senha, role))
            conn.commit()
            flash('Usuário criado com sucesso!', 'success')
        except sqlite3.IntegrityError:
            flash('Erro: O e-mail informado já existe.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('usuarios'))
    return render_template('new_usuario.html')

@app.route('/edit_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin_only')
def edit_usuario(id):
    conn = get_db_connection()
    usuario = conn.execute('SELECT id, nome, email, role FROM usuarios WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        nome, email, role, senha = request.form['nome'], request.form['email'], request.form['role'], request.form.get('senha')
        try:
            if senha:
                conn.execute('UPDATE usuarios SET nome = ?, email = ?, role = ?, senha = ? WHERE id = ?', (nome, email, role, generate_password_hash(senha), id))
            else:
                conn.execute('UPDATE usuarios SET nome = ?, email = ?, role = ? WHERE id = ?', (nome, email, role, id))
            conn.commit()
            flash('Usuário atualizado!', 'success')
        except sqlite3.IntegrityError:
            flash('Erro: O e-mail informado já pertence a outro usuário.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('usuarios'))
    conn.close()
    return render_template('edit_usuario.html', usuario=usuario)

@app.route('/delete_usuario/<int:id>', methods=['POST'])
@login_required
@role_required('admin_only')
def delete_usuario(id):
    if id == session.get('user_id'):
        flash('Você não pode excluir seu próprio usuário.', 'danger')
        return redirect(url_for('usuarios'))
    conn = get_db_connection()
    conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Usuário excluído.', 'success')
    return redirect(url_for('usuarios'))


if __name__ == '__main__':
    app.run(debug=True)