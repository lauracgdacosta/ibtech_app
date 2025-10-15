

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import datetime
import re

app = Flask(__name__)
app.secret_key = '18T3ch'

# --- LISTA MESTRA DE MÓDULOS ---
AVAILABLE_MODULES = {
    'cadastros': 'Cadastros (Técnicos, Clientes, etc)',
    'agenda': 'Agenda',
    'projetos': 'Projetos de Implantação',
    'pendencias': 'Pendências',
    'prestacao_contas': 'Prestação de Contas',
    'ferias': 'Férias',
    'matriz': 'Matriz de Responsabilidades'
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
    cursor.execute('''CREATE TABLE IF NOT EXISTS tecnicos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT, telefone TEXT, funcao TEXT, equipe TEXT, contrato TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, municipio TEXT NOT NULL, orgao TEXT, contrato TEXT, sistemas TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS equipes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, sigla TEXT, lider TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pendencias (id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo TEXT, data_registro TEXT, cliente TEXT, sistema TEXT, detalhamento TEXT, responsavel TEXT, fase TEXT, status TEXT, prioridade TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ferias (id INTEGER PRIMARY KEY AUTOINCREMENT, funcionario TEXT NOT NULL, admissao TEXT, contrato TEXT, ano INTEGER, data_inicio TEXT, data_termino TEXT, obs TEXT, status TEXT NOT NULL DEFAULT 'Planejada')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sistemas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, sigla TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS agenda (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT NOT NULL, tecnico TEXT NOT NULL, sistema TEXT, data_agendamento DATE NOT NULL, horario_agendamento TEXT, motivo TEXT, descricao TEXT, status TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS prestacao_contas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, sistema TEXT, responsavel TEXT, modulo TEXT, competencia TEXT, status TEXT, observacao TEXT, atualizado_por TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS projetos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, cliente TEXT, data_inicio_previsto DATE, data_termino_previsto DATE, status TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tarefas (id INTEGER PRIMARY KEY AUTOINCREMENT, projeto_id INTEGER NOT NULL, tipo TEXT NOT NULL, atividade_id TEXT, descricao TEXT NOT NULL, data_inicio DATE, data_termino DATE, responsavel_pm TEXT, responsavel_cm TEXT, status TEXT NOT NULL, local_execucao TEXT, observacoes TEXT, predecessoras TEXT, FOREIGN KEY (projeto_id) REFERENCES projetos (id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, nivel_acesso TEXT NOT NULL, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS matriz_responsabilidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            sistema TEXT NOT NULL,
            responsavel1 TEXT NOT NULL,
            responsavel2 TEXT,
            observacoes TEXT
        )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            role_name TEXT NOT NULL, 
            module_name TEXT NOT NULL, 
            can_read BOOLEAN DEFAULT 0, 
            can_create BOOLEAN DEFAULT 0,
            can_edit BOOLEAN DEFAULT 0, 
            can_delete BOOLEAN DEFAULT 0, 
            UNIQUE(role_name, module_name)
        )''')
    conn.commit()
    conn.close()

def migrate_agenda_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(agenda)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'horario_agendamento' not in columns:
            cursor.execute("ALTER TABLE agenda ADD COLUMN horario_agendamento TEXT")
            conn.commit()
    except Exception as e:
        print(f"ERRO ao migrar a tabela agenda: {e}")
    finally:
        conn.close()

def migrate_ferias_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(ferias)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'status' not in columns:
            cursor.execute("ALTER TABLE ferias ADD COLUMN status TEXT NOT NULL DEFAULT 'Planejada'")
            conn.commit()
    except Exception as e:
        print(f"ERRO ao migrar a tabela ferias: {e}")
    finally:
        conn.close()
        
def migrate_pendencias_add_prioridade():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(pendencias)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'prioridade' not in columns:
            print("MIGRATE: Adicionando coluna 'prioridade' à tabela 'pendencias'.")
            cursor.execute("ALTER TABLE pendencias ADD COLUMN prioridade TEXT")
            conn.commit()
            print("MIGRATE: Coluna 'prioridade' adicionada com sucesso.")
    except Exception as e:
        print(f"ERRO ao migrar a tabela pendencias para 'prioridade': {e}")
    finally:
        conn.close()

def migrate_pendencias_add_unique_protocolo():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print("MIGRATE: Verificando/Criando índice único para 'protocolo' na tabela 'pendencias'.")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pendencias_protocolo ON pendencias(protocolo)")
        conn.commit()
        print("MIGRATE: Índice único para 'protocolo' garantido.")
    except Exception as e:
        print(f"ERRO ao criar índice único para 'protocolo': {e}")
        conn.rollback()
    finally:
        conn.close()

def migrate_tarefas_add_predecessoras():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(tarefas)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'predecessoras' not in columns:
            print("MIGRATE: Adicionando coluna 'predecessoras' à tabela 'tarefas'.")
            cursor.execute("ALTER TABLE tarefas ADD COLUMN predecessoras TEXT")
            conn.commit()
            print("MIGRATE: Coluna 'predecessoras' adicionada com sucesso.")
    except Exception as e:
        print(f"ERRO ao migrar a tabela tarefas para 'predecessoras': {e}")
    finally:
        conn.close()

def migrate_pendencias_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(pendencias)")
        columns = [row['name'] for row in cursor.fetchall()]

        if 'processo' in columns:
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute('''
                CREATE TABLE pendencias_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    protocolo TEXT,
                    data_registro TEXT,
                    cliente TEXT,
                    sistema TEXT,
                    detalhamento TEXT,
                    responsavel TEXT,
                    fase TEXT,
                    status TEXT,
                    prioridade TEXT
                )
            ''')
            cursor.execute('''
                INSERT INTO pendencias_new (id, protocolo, cliente, sistema, status)
                SELECT id, processo, cliente, sistema, status FROM pendencias
            ''')
            cursor.execute("DROP TABLE pendencias")
            cursor.execute("ALTER TABLE pendencias_new RENAME TO pendencias")
            conn.commit()
    except Exception as e:
        print(f"ERRO ao migrar a tabela pendencias: {e}")
        conn.rollback()
    finally:
        conn.close()

def migrate_db_roles():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT role FROM usuarios LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN role TEXT")
    cursor.execute("UPDATE usuarios SET role = CASE WHEN nivel_acesso = 'Admin' THEN 'admin' WHEN nivel_acesso = 'Usuario' THEN 'tecnico' ELSE role END WHERE role IS NULL")
    if cursor.execute("SELECT COUNT(id) FROM usuarios").fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (nome, email, senha, role, nivel_acesso) VALUES (?, ?, ?, ?, ?)", ('Administrador', 'admin@ibtech.com', generate_password_hash("admin"), 'admin', 'Admin'))
    conn.commit()
    conn.close()

def migrate_permissions_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT can_read FROM role_permissions LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE role_permissions ADD COLUMN can_read BOOLEAN DEFAULT 0")
            cursor.execute("ALTER TABLE role_permissions ADD COLUMN can_edit BOOLEAN DEFAULT 0")
            cursor.execute("ALTER TABLE role_permissions ADD COLUMN can_delete BOOLEAN DEFAULT 0")
            cursor.execute("UPDATE role_permissions SET can_read = 1, can_edit = 1, can_delete = 1")
            conn.commit()
        except Exception as e:
            print(f"ERRO MIGRATE: {e}")
            conn.rollback()
    finally:
        conn.close()

def migrate_permissions_for_create():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(role_permissions)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'can_create' not in columns:
            cursor.execute("ALTER TABLE role_permissions ADD COLUMN can_create BOOLEAN DEFAULT 0")
            cursor.execute("UPDATE role_permissions SET can_create = can_edit")
            conn.commit()
    except Exception as e:
        print(f"ERRO ao migrar a tabela role_permissions para 'can_create': {e}")
    finally:
        conn.close()


with app.app_context():
    init_db()
    migrate_db_roles()
    migrate_permissions_table()
    migrate_agenda_table()
    migrate_ferias_table()
    migrate_pendencias_table()
    migrate_permissions_for_create()
    migrate_pendencias_add_prioridade()
    migrate_pendencias_add_unique_protocolo()
    migrate_tarefas_add_predecessoras()

# --- LÓGICA E DECORADORES DE PERMISSÃO ---
def check_permission(module_name, action):
    user_role = session.get('user_role')
    if not user_role: return False
    if user_role == 'admin': return True
    conn = get_db_connection()
    query = f"SELECT {action} FROM role_permissions WHERE role_name = ? AND module_name = ?"
    permission = conn.execute(query, (user_role, module_name)).fetchone()
    conn.close()
    return permission and permission[0] == 1

@app.context_processor
def inject_user_permissions():
    return dict(check_permission=check_permission)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(module, action):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_permission(module, action):
                flash('Você não tem permissão para realizar esta ação.', 'danger')
                return redirect(request.referrer or url_for('index'))
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
    pendencias_abertas = conn.execute("SELECT * FROM pendencias WHERE status = 'Pendente' ORDER BY data_registro DESC LIMIT 5").fetchall()
    tecnicos_em_ferias = conn.execute('SELECT * FROM ferias WHERE data_inicio <= ? AND data_termino >= ?', (hoje_str, hoje_str)).fetchall()
    
    protocolos_por_sistema_data = conn.execute(
        "SELECT sistema, COUNT(id) as total FROM pendencias GROUP BY sistema ORDER BY total DESC"
    ).fetchall()
    protocolos_por_sistema = [{'sistema': row['sistema'], 'total': row['total']} for row in protocolos_por_sistema_data]

    protocolos_por_cliente_data = conn.execute(
        "SELECT cliente, COUNT(id) as total FROM pendencias GROUP BY cliente ORDER BY total DESC"
    ).fetchall()
    protocolos_por_cliente = [{'cliente': row['cliente'], 'total': row['total']} for row in protocolos_por_cliente_data]
    
    conn.close()
    
    return render_template('index.html', 
                           proximos_agendamentos=proximos_agendamentos, 
                           pendencias_abertas=pendencias_abertas, 
                           tecnicos_em_ferias=tecnicos_em_ferias,
                           protocolos_por_sistema=protocolos_por_sistema,
                           protocolos_por_cliente=protocolos_por_cliente)

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
            session['user_id'], session['user_name'], session['user_role'] = usuario['id'], usuario['nome'], usuario['role']
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))
    
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        senha_atual = request.form['senha_atual']
        nova_senha = request.form['nova_senha']
        confirmacao_nova_senha = request.form['confirmacao_nova_senha']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not user or not check_password_hash(user['senha'], senha_atual):
            flash('Senha atual incorreta.', 'danger')
            conn.close()
            return redirect(url_for('change_password'))
        
        if nova_senha != confirmacao_nova_senha:
            flash('A nova senha e a confirmação não correspondem.', 'danger')
            conn.close()
            return redirect(url_for('change_password'))

        nova_senha_hash = generate_password_hash(nova_senha)
        conn.execute('UPDATE usuarios SET senha = ? WHERE id = ?', (nova_senha_hash, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('index'))
        
    return render_template('change_password.html')

# --- ROTAS DE GESTÃO (Admin) ---
@app.route('/gerenciar_permissoes')
@login_required
@role_required(module='admin_only', action='can_edit')
def gerenciar_permissoes():
    conn = get_db_connection()
    permissions_data = conn.execute('SELECT role_name, module_name, can_read, can_create, can_edit, can_delete FROM role_permissions').fetchall()
    conn.close()
    permissions = {}
    for p in permissions_data:
        role, module = p['role_name'], p['module_name']
        if role not in permissions: permissions[role] = {}
        permissions[role][module] = {
            'can_read': p['can_read'], 
            'can_create': p['can_create'], 
            'can_edit': p['can_edit'], 
            'can_delete': p['can_delete']
        }
    roles_to_manage = ['coordenacao', 'tecnico']
    return render_template('gerenciar_permissoes.html', modules=AVAILABLE_MODULES, roles=roles_to_manage, current_permissions=permissions)

@app.route('/salvar_permissoes', methods=['POST'])
@login_required
@role_required(module='admin_only', action='can_edit')
def salvar_permissoes():
    conn = get_db_connection()
    cursor = conn.cursor()
    roles_to_manage = ['coordenacao', 'tecnico']
    
    try:
        cursor.execute(f"DELETE FROM role_permissions WHERE role_name IN ({','.join('?'*len(roles_to_manage))})", roles_to_manage)
        
        for role in roles_to_manage:
            for module_key in AVAILABLE_MODULES.keys():
                can_read = 1 if f'permission_{role}_{module_key}_can_read' in request.form else 0
                can_create = 1 if f'permission_{role}_{module_key}_can_create' in request.form else 0
                can_edit = 1 if f'permission_{role}_{module_key}_can_edit' in request.form else 0
                can_delete = 1 if f'permission_{role}_{module_key}_can_delete' in request.form else 0
                
                if can_read or can_create or can_edit or can_delete:
                    cursor.execute('INSERT INTO role_permissions (role_name, module_name, can_read, can_create, can_edit, can_delete) VALUES (?, ?, ?, ?, ?, ?)', 
                                   (role, module_key, can_read, can_create, can_edit, can_delete))
        
        conn.commit()
        flash('Permissões atualizadas com sucesso!', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Ocorreu um erro ao salvar as permissões: {e}', 'danger')
        print(f"!!!!!!!!!!!! ERRO AO SALVAR PERMISSÕES: {e} !!!!!!!!!!!!")

    finally:
        conn.close()
        
    return redirect(url_for('gerenciar_permissoes'))
    

# --- MÓDULOS DE CADASTRO ---
@app.route('/cadastros')
@login_required
@role_required(module='cadastros', action='can_read')
def cadastros():
    return render_template('cadastros.html')

@app.route('/tecnicos')
@login_required
@role_required(module='cadastros', action='can_read')
def tecnicos():
    conn = get_db_connection()

    per_page = 20
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'nome', type=str)
    order = request.args.get('order', 'asc', type=str)

    # Filtros
    search_nome = request.args.get('search_nome', '', type=str)
    search_email = request.args.get('search_email', '', type=str)
    search_funcao = request.args.get('search_funcao', '', type=str)
    search_equipe = request.args.get('search_equipe', '', type=str)
    search_contrato = request.args.get('search_contrato', '', type=str)

    allowed_sort_columns = ['nome', 'email', 'telefone', 'funcao', 'equipe', 'contrato']
    if sort_by not in allowed_sort_columns:
        sort_by = 'nome'
    if order.lower() not in ['asc', 'desc']:
        order = 'asc'

    offset = (page - 1) * per_page
    base_query = "FROM tecnicos WHERE 1=1"
    params = []

    if search_nome:
        base_query += " AND nome LIKE ?"
        params.append(f"%{search_nome}%")
    if search_email:
        base_query += " AND email LIKE ?"
        params.append(f"%{search_email}%")
    if search_funcao:
        base_query += " AND funcao LIKE ?"
        params.append(f"%{search_funcao}%")
    if search_equipe:
        base_query += " AND equipe LIKE ?"
        params.append(f"%{search_equipe}%")
    if search_contrato:
        base_query += " AND contrato LIKE ?"
        params.append(f"%{search_contrato}%")

    total_query = "SELECT COUNT(id) " + base_query
    total_results = conn.execute(total_query, tuple(params)).fetchone()[0]
    total_pages = (total_results + per_page - 1) // per_page
    data_query = f"SELECT * {base_query} ORDER BY {sort_by} {order} LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    tecnicos_data = conn.execute(data_query, tuple(params)).fetchall()

    conn.close()

    pagination_args = request.args.to_dict()
    if 'page' in pagination_args: del pagination_args['page']
    sorting_args = request.args.to_dict()
    if 'sort_by' in sorting_args: del sorting_args['sort_by']
    if 'order' in sorting_args: del sorting_args['order']

    return render_template('tecnicos.html',
                           tecnicos=tecnicos_data,
                           page=page, total_pages=total_pages,
                           sort_by=sort_by, order=order,
                           search_nome=search_nome,
                           search_email=search_email,
                           search_funcao=search_funcao,
                           search_equipe=search_equipe,
                           search_contrato=search_contrato,
                           pagination_args=pagination_args,
                           sorting_args=sorting_args)

def build_tecnicos_redirect_url():
    args = {}
    valid_state_keys = ['search_nome', 'search_email', 'search_funcao', 'search_equipe', 'search_contrato', 'page', 'sort_by', 'order']
    for key in valid_state_keys:
        value = request.form.get(key)
        if value:
            args[key] = value
    return url_for('tecnicos', **args)

@app.route('/new_tecnico', methods=['GET', 'POST'])
@login_required
@role_required(module='cadastros', action='can_create') # Alterado de 'can_edit' para 'can_create'
def new_tecnico():
    args = request.args.to_dict()
    conn = get_db_connection()
    if request.method == 'POST':
        form = request.form
        conn.execute('INSERT INTO tecnicos (nome, email, telefone, funcao, equipe, contrato) VALUES (?, ?, ?, ?, ?, ?)',
                     (form['nome'], form['email'], form['telefone'], form['funcao'], form['equipe'], form['contrato']))
        conn.commit()
        conn.close()
        flash('Novo técnico criado com sucesso!', 'success')
        return redirect(build_tecnicos_redirect_url())

    equipes = conn.execute('SELECT nome FROM equipes ORDER BY nome').fetchall()
    conn.close()
    return render_template('new_tecnico.html', equipes=equipes, args=args)

@app.route('/edit_tecnico/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(module='cadastros', action='can_edit')
def edit_tecnico(id):
    args = request.args.to_dict()
    conn = get_db_connection()
    tecnico = conn.execute('SELECT * FROM tecnicos WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        form = request.form
        conn.execute('UPDATE tecnicos SET nome=?, email=?, telefone=?, funcao=?, equipe=?, contrato=? WHERE id=?',
                     (form['nome'], form['email'], form['telefone'], form['funcao'], form['equipe'], form['contrato'], id))
        conn.commit()
        conn.close()
        flash('Técnico atualizado com sucesso!', 'success')
        return redirect(build_tecnicos_redirect_url())

    equipes = conn.execute('SELECT nome FROM equipes ORDER BY nome').fetchall()
    conn.close()
    return render_template('edit_tecnico.html', tecnico=tecnico, equipes=equipes, args=args)

@app.route('/delete_tecnico/<int:id>', methods=['POST'])
@login_required
@role_required(module='cadastros', action='can_delete')
def delete_tecnico(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tecnicos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Técnico excluído com sucesso.', 'success')
    return redirect(build_tecnicos_redirect_url())

@app.route('/clientes')
@login_required
@role_required(module='cadastros', action='can_read')
def clientes():
    conn = get_db_connection()
    clientes_data = conn.execute('SELECT * FROM clientes').fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes_data)

@app.route('/new_cliente', methods=['GET', 'POST'])
@login_required
@role_required(module='cadastros', action='can_create')
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
@role_required(module='cadastros', action='can_edit')
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
@role_required(module='cadastros', action='can_delete')
def delete_cliente(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM clientes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('clientes'))

@app.route('/equipes')
@login_required
@role_required(module='cadastros', action='can_read')
def equipes():
    conn = get_db_connection()
    equipes_data = conn.execute('SELECT * FROM equipes').fetchall()
    conn.close()
    return render_template('equipes.html', equipes=equipes_data)

@app.route('/new_equipe', methods=['GET', 'POST'])
@login_required
@role_required(module='cadastros', action='can_create')
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
@role_required(module='cadastros', action='can_edit')
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
@role_required(module='cadastros', action='can_delete')
def delete_equipe(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM equipes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('equipes'))

@app.route('/sistemas')
@login_required
@role_required(module='cadastros', action='can_read')
def sistemas():
    conn = get_db_connection()
    sistemas_data = conn.execute('SELECT * FROM sistemas').fetchall()
    conn.close()
    return render_template('sistemas.html', sistemas=sistemas_data)

@app.route('/new_sistema', methods=['GET', 'POST'])
@login_required
@role_required(module='cadastros', action='can_create')
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
@role_required(module='cadastros', action='can_edit')
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
@role_required(module='cadastros', action='can_delete')
def delete_sistema(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM sistemas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('sistemas'))

# --- MÓDULO DE PROJETOS (com as novas alterações) ---
@app.route('/projetos')
@login_required
@role_required(module='projetos', action='can_read')
def projetos():
    conn = get_db_connection()
    projetos_db = conn.execute('SELECT * FROM projetos ORDER BY id DESC').fetchall()
    conn.close()

    projetos_processados = []
    hoje = datetime.date.today()

    for projeto_row in projetos_db:
        projeto = dict(projeto_row)
        data_inicio = datetime.datetime.strptime(projeto['data_inicio_previsto'], '%Y-%m-%d').date() if projeto['data_inicio_previsto'] else None
        data_termino = datetime.datetime.strptime(projeto['data_termino_previsto'], '%Y-%m-%d').date() if projeto['data_termino_previsto'] else None

        if data_termino and hoje >= data_termino:
            projeto['status'] = 'Concluído'
        elif data_inicio and hoje >= data_inicio:
            projeto['status'] = 'Em Andamento'
        
        projetos_processados.append(projeto)

    return render_template('projetos.html', projetos=projetos_processados)

@app.route('/new_projeto', methods=['GET', 'POST'])
@login_required
@role_required(module='projetos', action='can_create')
def new_projeto():
    conn = get_db_connection()
    if request.method == 'POST':
        form = request.form
        cursor = conn.cursor()
        cursor.execute('INSERT INTO projetos (nome, cliente, data_inicio_previsto, data_termino_previsto, status) VALUES (?, ?, ?, ?, ?)',
                     (form['nome'], form['cliente'], form['data_inicio_previsto'], form['data_termino_previsto'], form['status']))
        novo_projeto_id = cursor.lastrowid
        for tarefa in TAREFAS_PADRAO:
            cursor.execute('INSERT INTO tarefas (projeto_id, atividade_id, descricao, tipo, status) VALUES (?, ?, ?, ?, ?)',
                         (novo_projeto_id, tarefa['id'], tarefa['desc'], tarefa['tipo'], 'Planejada'))
        conn.commit()
        conn.close()
        flash('Projeto criado com sucesso e checklist padrão adicionado!', 'success')
        return redirect(url_for('projetos'))
    
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    clientes = [f"{row['municipio']} - {row['orgao']}" for row in clientes_data]
    conn.close()
    return render_template('new_projeto.html', clientes=clientes)

@app.route('/projeto/edit/<int:projeto_id>', methods=['GET', 'POST'])
@login_required
@role_required(module='projetos', action='can_edit')
def edit_projeto(projeto_id):
    conn = get_db_connection()
    projeto = conn.execute('SELECT * FROM projetos WHERE id = ?', (projeto_id,)).fetchone()
    if request.method == 'POST':
        form = request.form
        conn.execute('UPDATE projetos SET nome = ?, cliente = ?, data_inicio_previsto = ?, data_termino_previsto = ?, status = ? WHERE id = ?',
                     (form['nome'], form['cliente'], form['data_inicio_previsto'], form['data_termino_previsto'], form['status'], projeto_id))
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
@role_required(module='projetos', action='can_delete')
def delete_projeto(projeto_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM projetos WHERE id = ?', (projeto_id,))
    conn.commit()
    conn.close()
    flash('Projeto e tarefas excluídos!', 'success')
    return redirect(url_for('projetos'))

@app.route('/projeto/<int:projeto_id>')
@login_required
@role_required(module='projetos', action='can_read')
def checklist_projeto(projeto_id):
    conn = get_db_connection()
    projeto = conn.execute('SELECT * FROM projetos WHERE id = ?', (projeto_id,)).fetchone()
    tarefas_from_db = conn.execute('SELECT * FROM tarefas WHERE projeto_id = ? ORDER BY atividade_id', (projeto_id,)).fetchall()
    
    tarefas_processadas = []
    for tarefa_row in tarefas_from_db:
        tarefa = dict(tarefa_row)
        duracao = "N/D"
        if tarefa['data_inicio'] and tarefa['data_termino']:
            try:
                inicio = datetime.datetime.strptime(tarefa['data_inicio'], '%Y-%m-%d')
                termino = datetime.datetime.strptime(tarefa['data_termino'], '%Y-%m-%d')
                delta = (termino - inicio).days
                if delta < 0:
                    duracao = "Inválido"
                else:
                    dias_totais = delta + 1
                    sufixo = 's' if dias_totais > 1 else ''
                    duracao = f"{dias_totais} dia{sufixo}"
            except (ValueError, TypeError):
                duracao = "Inválido"
        tarefa['duracao_calculada'] = duracao
        tarefas_processadas.append(tarefa)

    conn.close()
    if not projeto:
        flash('Projeto não encontrado.', 'danger')
        return redirect(url_for('projetos'))
    
    return render_template('checklist_projeto.html', projeto=projeto, tarefas=tarefas_processadas)

@app.route('/tarefa/edit/<int:tarefa_id>', methods=['GET', 'POST'])
@login_required
@role_required(module='projetos', action='can_edit')
def edit_tarefa(tarefa_id):
    conn = get_db_connection()
    tarefa = conn.execute('SELECT * FROM tarefas WHERE id = ?', (tarefa_id,)).fetchone()
    if request.method == 'POST':
        form = request.form
        predecessoras_list = form.getlist('predecessoras')
        predecessoras_str = ', '.join(predecessoras_list)
        
        conn.execute('''
            UPDATE tarefas SET atividade_id = ?, descricao = ?, data_inicio = ?, data_termino = ?, 
            responsavel_pm = ?, responsavel_cm = ?, status = ?, local_execucao = ?, observacoes = ?, predecessoras = ? WHERE id = ?
        ''', (form['atividade_id'], form['descricao'], form['data_inicio'] or None, form['data_termino'] or None, 
              form['responsavel_pm'], form['responsavel_cm'], form['status'], form['local_execucao'], form['observacoes'], 
              predecessoras_str, tarefa_id))
        conn.commit()
        conn.close()
        flash('Tarefa atualizada!', 'success')
        return redirect(url_for('checklist_projeto', projeto_id=tarefa['projeto_id']))
    
    all_tasks = conn.execute("SELECT atividade_id, descricao FROM tarefas WHERE projeto_id = ? AND tipo = 'tarefa' AND id != ? ORDER BY atividade_id", (tarefa['projeto_id'], tarefa_id)).fetchall()
    tecnicos = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    clientes_data = conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()
    locais = sorted(list(set([f"{c['municipio']} - {c['orgao']}" for c in clientes_data] + ['Ibtech'])))
    conn.close()
    return render_template('edit_tarefa.html', tarefa=tarefa, tecnicos=tecnicos, locais=locais, all_tasks=all_tasks)

@app.route('/tarefa/delete/<int:tarefa_id>', methods=['POST'])
@login_required
@role_required(module='projetos', action='can_delete')
def delete_tarefa(tarefa_id):
    conn = get_db_connection()
    tarefa = conn.execute('SELECT projeto_id FROM tarefas WHERE id = ?', (tarefa_id,)).fetchone()
    projeto_id = tarefa['projeto_id'] if tarefa else None
    conn.execute('DELETE FROM tarefas WHERE id = ?', (tarefa_id,))
    conn.commit()
    conn.close()
    flash('Tarefa excluída.', 'success')
    return redirect(url_for('checklist_projeto', projeto_id=projeto_id)) if projeto_id else redirect(url_for('projetos'))

@app.route('/tarefa/toggle_status/<int:tarefa_id>', methods=['POST'])
@login_required
@role_required(module='projetos', action='can_edit')
def toggle_tarefa_status(tarefa_id):
    conn = get_db_connection()
    tarefa = conn.execute('SELECT * FROM tarefas WHERE id = ?', (tarefa_id,)).fetchone()
    if tarefa:
        novo_status = 'Em Andamento' if tarefa['status'] == 'Concluída' else 'Concluída'
        conn.execute('UPDATE tarefas SET status = ? WHERE id = ?', (novo_status, tarefa_id))
        conn.commit()
    conn.close()
    return redirect(url_for('checklist_projeto', projeto_id=tarefa['projeto_id']))

@app.route('/projeto/<int:projeto_id>/new_tarefa', methods=['GET', 'POST'])
@login_required
@role_required(module='projetos', action='can_create')
def new_tarefa(projeto_id):
    conn = get_db_connection()
    if request.method == 'POST':
        form = request.form
        predecessoras_list = form.getlist('predecessoras')
        predecessoras_str = ', '.join(predecessoras_list)
        
        conn.execute(
            'INSERT INTO tarefas (projeto_id, tipo, status, atividade_id, descricao, responsavel_pm, responsavel_cm, predecessoras) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (projeto_id, 'tarefa', 'Planejada', form['atividade_id'], form['descricao'], form['responsavel_pm'], form['responsavel_cm'], predecessoras_str)
        )
        conn.commit()
        conn.close()
        flash('Nova tarefa adicionada com sucesso!', 'success')
        return redirect(url_for('checklist_projeto', projeto_id=projeto_id))
    
    projeto = conn.execute('SELECT * FROM projetos WHERE id = ?', (projeto_id,)).fetchone()
    all_tasks = conn.execute("SELECT atividade_id, descricao FROM tarefas WHERE projeto_id = ? AND tipo = 'tarefa' ORDER BY atividade_id", (projeto_id,)).fetchall()
    tecnicos = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    conn.close()
    return render_template('new_tarefa.html', projeto=projeto, tecnicos=tecnicos, all_tasks=all_tasks)

@app.route('/projeto/<int:projeto_id>/new_titulo', methods=['GET', 'POST'])
@login_required
@role_required(module='projetos', action='can_create')
def new_titulo(projeto_id):
    conn = get_db_connection()
    if request.method == 'POST':
        form = request.form
        conn.execute(
            'INSERT INTO tarefas (projeto_id, tipo, status, atividade_id, descricao) VALUES (?, ?, ?, ?, ?)',
            (projeto_id, 'titulo', 'N/A', form['atividade_id'], form['descricao'])
        )
        conn.commit()
        conn.close()
        flash('Novo título adicionado com sucesso!', 'success')
        return redirect(url_for('checklist_projeto', projeto_id=projeto_id))
    projeto = conn.execute('SELECT * FROM projetos WHERE id = ?', (projeto_id,)).fetchone()
    conn.close()
    return render_template('new_titulo.html', projeto=projeto)

@app.route('/titulo/edit/<int:tarefa_id>', methods=['GET', 'POST'])
@login_required
@role_required(module='projetos', action='can_edit')
def edit_titulo(tarefa_id):
    conn = get_db_connection()
    tarefa = conn.execute('SELECT * FROM tarefas WHERE id = ?', (tarefa_id,)).fetchone()
    if request.method == 'POST':
        form = request.form
        conn.execute('UPDATE tarefas SET atividade_id = ?, descricao = ? WHERE id = ?',
                     (form['atividade_id'], form['descricao'], tarefa_id))
        conn.commit()
        conn.close()
        flash('Título atualizado com sucesso!', 'success')
        return redirect(url_for('checklist_projeto', projeto_id=tarefa['projeto_id']))
    projeto = conn.execute('SELECT * FROM projetos WHERE id = ?', (tarefa['projeto_id'],)).fetchone()
    conn.close()
    return render_template('edit_titulo.html', projeto=projeto, tarefa=tarefa)


# --- MÓDULO DE PENDÊNCIAS (com validação e todas as melhorias) ---
@app.route('/pendencias')
@login_required
@role_required(module='pendencias', action='can_read')
def pendencias():
    conn = get_db_connection()
    
    page = request.args.get('page', 1, type=int)
    per_page_str = request.args.get('per_page', '20', type=str)

    if per_page_str.lower() == 'all':
        per_page = -1
    else:
        try:
            per_page = int(per_page_str)
        except ValueError:
            per_page = 20

    sort_by = request.args.get('sort_by', 'data_registro', type=str)
    order = request.args.get('order', 'desc', type=str)
    
    search_protocolo = request.args.get('search_protocolo', '', type=str)
    search_data_registro = request.args.get('search_data_registro', '', type=str)
    search_cliente = request.args.get('search_cliente', '', type=str)
    search_sistema = request.args.get('search_sistema', '', type=str)
    search_detalhamento = request.args.get('search_detalhamento', '', type=str)
    search_responsavel = request.args.get('search_responsavel', '', type=str)
    search_fase = request.args.get('search_fase', '', type=str)
    search_status = request.args.get('search_status', '', type=str)
    search_prioridade = request.args.get('search_prioridade', '', type=str)

    allowed_sort_columns = ['protocolo', 'data_registro', 'cliente', 'sistema', 'detalhamento', 'responsavel', 'fase', 'status', 'prioridade']
    if sort_by not in allowed_sort_columns:
        sort_by = 'data_registro'
    if order.lower() not in ['asc', 'desc']:
        order = 'desc'

    base_query = "FROM pendencias WHERE 1=1"
    params = []

    if search_protocolo:
        base_query += " AND protocolo LIKE ?"
        params.append(f"%{search_protocolo}%")
    if search_data_registro:
        base_query += " AND data_registro = ?"
        params.append(search_data_registro)
    if search_cliente:
        base_query += " AND cliente = ?"
        params.append(search_cliente)
    if search_sistema:
        base_query += " AND sistema = ?"
        params.append(search_sistema)
    if search_detalhamento:
        base_query += " AND detalhamento LIKE ?"
        params.append(f"%{search_detalhamento}%")
    if search_responsavel:
        base_query += " AND responsavel = ?"
        params.append(search_responsavel)
    if search_fase:
        base_query += " AND fase = ?"
        params.append(search_fase)
    if search_status:
        base_query += " AND status = ?"
        params.append(search_status)
    if search_prioridade:
        base_query += " AND prioridade = ?"
        params.append(search_prioridade)
    
    total_query = "SELECT COUNT(id) " + base_query
    total_results = conn.execute(total_query, tuple(params)).fetchone()[0]
    
    data_query = f"SELECT * {base_query} ORDER BY {sort_by} {order}"
    
    if per_page == -1:
        total_pages = 1
        page = 1
    else:
        total_pages = (total_results + per_page - 1) // per_page
        offset = (page - 1) * per_page
        data_query += " LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
    
    pendencias_data = conn.execute(data_query, tuple(params)).fetchall()
    
    clientes_list = conn.execute("SELECT DISTINCT cliente FROM pendencias WHERE cliente IS NOT NULL ORDER BY cliente").fetchall()
    sistemas_list = conn.execute("SELECT DISTINCT sistema FROM pendencias WHERE sistema IS NOT NULL ORDER BY sistema").fetchall()
    responsaveis_list = conn.execute("SELECT DISTINCT responsavel FROM pendencias WHERE responsavel IS NOT NULL ORDER BY responsavel").fetchall()
    
    conn.close()

    pagination_args = request.args.to_dict()
    if 'page' in pagination_args: del pagination_args['page']
    sorting_args = request.args.to_dict()
    if 'sort_by' in sorting_args: del sorting_args['sort_by']
    if 'order' in sorting_args: del sorting_args['order']

    return render_template('pendencias.html', 
                           pendencias=pendencias_data,
                           page=page, total_pages=total_pages,
                           sort_by=sort_by, order=order,
                           search_protocolo=search_protocolo,
                           search_data_registro=search_data_registro,
                           search_cliente=search_cliente,
                           search_sistema=search_sistema,
                           search_detalhamento=search_detalhamento,
                           search_responsavel=search_responsavel,
                           search_fase=search_fase,
                           search_status=search_status,
                           search_prioridade=search_prioridade,
                           clientes_list=clientes_list,
                           sistemas_list=sistemas_list,
                           responsaveis_list=responsaveis_list,
                           pagination_args=pagination_args,
                           sorting_args=sorting_args,
                           per_page=per_page_str)

def build_pendencias_redirect_url():
    args = {}
    valid_state_keys = [
        'search_protocolo', 'search_cliente', 'search_sistema', 
        'search_responsavel', 'search_fase', 'search_status', 
        'search_prioridade', 'page', 'sort_by', 'order'
    ]
    for key in valid_state_keys:
        value = request.values.get(key)
        if value:
            args[key] = value
    return url_for('pendencias', **args)

@app.route('/new_pendencia', methods=['GET', 'POST'])
@login_required
@role_required(module='pendencias', action='can_create')
def new_pendencia():
    args = request.args.to_dict()
    conn = get_db_connection()

    if request.method == 'POST':
        form = request.form
        
        numero_digitado = form['protocolo']
        ano_atual = str(datetime.date.today().year)
        protocolo_final = f"{numero_digitado.zfill(6)}/{ano_atual}"

        existing_pendencia = conn.execute('SELECT id FROM pendencias WHERE protocolo = ?', (protocolo_final,)).fetchone()
        if existing_pendencia:
            flash('Erro: O protocolo informado já existe no sistema.', 'danger')
            clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
            sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
            responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
            conn.close()
            return render_template('new_pendencia.html', 
                                   form_data=form,
                                   clientes=clientes,
                                   sistemas=sistemas,
                                   responsaveis=responsaveis,
                                   args=args, 
                                   ano_atual=ano_atual)

        try:
            conn.execute('INSERT INTO pendencias (protocolo, data_registro, cliente, sistema, detalhamento, responsavel, fase, status, prioridade) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                         (protocolo_final, form['data_registro'], form['cliente'], form['sistema'], form['detalhamento'], form['responsavel'], form['fase'], form['status'], form['prioridade']))
            conn.commit()
            flash(f'Nova demanda criada com sucesso! Protocolo: {protocolo_final}', 'success')
        except sqlite3.IntegrityError:
            conn.rollback()
            flash('Erro: O protocolo informado já existe no sistema. (Erro de banco de dados)', 'danger')
        finally:
            conn.close()
            
        return redirect(build_pendencias_redirect_url())
    
    clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    conn.close()
    
    ano_atual = str(datetime.date.today().year)
    
    return render_template('new_pendencia.html', clientes=clientes, sistemas=sistemas, responsaveis=responsaveis, args=args, ano_atual=ano_atual, form_data={})

@app.route('/edit_pendencia/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(module='pendencias', action='can_edit')
def edit_pendencia(id):
    args = request.args.to_dict()
    conn = get_db_connection()
    
    if request.method == 'POST':
        form = request.form
        
        numero_protocolo_editado = form['protocolo_numero']
        ano_protocolo = form['protocolo_ano']
        protocolo_final = f"{numero_protocolo_editado.zfill(6)}/{ano_protocolo}"

        existing_pendencia = conn.execute('SELECT id FROM pendencias WHERE protocolo = ? AND id != ?', (protocolo_final, id)).fetchone()
        if existing_pendencia:
            flash('Erro: O protocolo informado já pertence a outra demanda.', 'danger')
            conn.close()
            return redirect(url_for('edit_pendencia', id=id, **args))

        try:
            conn.execute('UPDATE pendencias SET protocolo=?, data_registro=?, cliente=?, sistema=?, detalhamento=?, responsavel=?, fase=?, status=?, prioridade=? WHERE id=?',
                         (protocolo_final, form['data_registro'], form['cliente'], form['sistema'], form['detalhamento'], form['responsavel'], form['fase'], form['status'], form['prioridade'], id))
            conn.commit()
            flash('Demanda atualizada com sucesso!', 'success')
        except sqlite3.IntegrityError:
            conn.rollback()
            flash('Erro: O protocolo informado já pertence a outra demanda. (Erro de banco de dados)', 'danger')
        finally:
            conn.close()
            
        return redirect(build_pendencias_redirect_url())
        
    pendencia = conn.execute('SELECT * FROM pendencias WHERE id = ?', (id,)).fetchone()
    clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    conn.close()

    numero_protocolo, ano_protocolo = "", ""
    if pendencia and pendencia['protocolo'] and '/' in pendencia['protocolo']:
        partes = pendencia['protocolo'].split('/')
        numero_protocolo = partes[0]
        ano_protocolo = partes[1]

    return render_template('edit_pendencia.html', 
                           pendencia=pendencia, 
                           clientes=clientes, 
                           sistemas=sistemas, 
                           responsaveis=responsaveis, 
                           args=args,
                           numero_protocolo=numero_protocolo,
                           ano_protocolo=ano_protocolo)


@app.route('/delete_pendencia/<int:id>', methods=['POST'])
@login_required
@role_required(module='pendencias', action='can_delete')
def delete_pendencia(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM pendencias WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Demanda excluída com sucesso.', 'success')
    return redirect(build_pendencias_redirect_url())

# --- MÓDULO DE FÉRIAS ---
# SUBSTITUA TODA A SUA FUNÇÃO ferias() POR ESTA VERSÃO CORRIGIDA

@app.route('/ferias')
@login_required
@role_required(module='ferias', action='can_read')
def ferias():
    conn = get_db_connection()
    
    per_page = 20
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'data_inicio', type=str)
    order = request.args.get('order', 'desc', type=str)
    
    # Filtros existentes e novos
    search_funcionario = request.args.get('search_funcionario', '', type=str)
    search_contrato = request.args.get('search_contrato', '', type=str)
    search_ano = request.args.get('search_ano', '', type=str)
    search_obs = request.args.get('search_obs', '', type=str)
    search_status = request.args.get('search_status', '', type=str)
    search_admissao = request.args.get('search_admissao', '', type=str)
    search_data_inicio = request.args.get('search_data_inicio', '', type=str)
    search_data_termino = request.args.get('search_data_termino', '', type=str)

    allowed_sort_columns = ['funcionario', 'admissao', 'contrato', 'ano', 'data_inicio', 'data_termino', 'obs', 'status']
    if sort_by not in allowed_sort_columns:
        sort_by = 'data_inicio'
    if order.lower() not in ['asc', 'desc']:
        order = 'desc'

    offset = (page - 1) * per_page
    
    ferias_db = conn.execute('SELECT * FROM ferias').fetchall()
    conn.close()

    ferias_processadas = []
    hoje = datetime.date.today()

    for ferias_row in ferias_db:
        item = dict(ferias_row)
        
        # --- ALTERAÇÃO APLICADA AQUI ---
        # Adicionado tratamento de erro para datas inválidas
        try:
            data_inicio = datetime.datetime.strptime(item['data_inicio'], '%Y-%m-%d').date() if item['data_inicio'] else None
        except (ValueError, TypeError):
            data_inicio = None # Define como None se o formato for inválido

        try:
            data_termino = datetime.datetime.strptime(item['data_termino'], '%Y-%m-%d').date() if item['data_termino'] else None
        except (ValueError, TypeError):
            data_termino = None # Define como None se o formato for inválido
        # --- FIM DA ALTERAÇÃO ---

        if data_termino and hoje > data_termino:
            item['status'] = 'Concluído'
        elif data_inicio and data_termino and data_inicio <= hoje <= data_termino:
            item['status'] = 'Em Andamento'
        else:
            item['status'] = 'Planejada'
        
        # Aplica os filtros
        if (search_funcionario and search_funcionario.lower() not in item['funcionario'].lower()): continue
        if (search_contrato and search_contrato.lower() not in (item['contrato'] or '').lower()): continue
        if (search_ano and str(item['ano']) != search_ano): continue
        if (search_obs and search_obs.lower() not in (item['obs'] or '').lower()): continue
        if (search_status and item['status'] != search_status): continue
        if (search_admissao and item['admissao'] != search_admissao): continue
        if (search_data_inicio and item['data_inicio'] != search_data_inicio): continue
        if (search_data_termino and item['data_termino'] != search_data_termino): continue

        ferias_processadas.append(item)

    # Ordenação
    ferias_processadas.sort(key=lambda x: str(x.get(sort_by) or ''), reverse=(order == 'desc'))

    # Paginação
    total_results = len(ferias_processadas)
    total_pages = (total_results + per_page - 1) // per_page
    ferias_paginadas = ferias_processadas[offset : offset + per_page]

    pagination_args = request.args.to_dict()
    if 'page' in pagination_args: del pagination_args['page']
    sorting_args = request.args.to_dict()
    if 'sort_by' in sorting_args: del sorting_args['sort_by']
    if 'order' in sorting_args: del sorting_args['order']

    return render_template('ferias.html', 
                           ferias=ferias_paginadas, page=page, total_pages=total_pages,
                           sort_by=sort_by, order=order,
                           search_funcionario=search_funcionario,
                           search_contrato=search_contrato,
                           search_ano=search_ano,
                           search_obs=search_obs,
                           search_status=search_status,
                           search_admissao=search_admissao,
                           search_data_inicio=search_data_inicio,
                           search_data_termino=search_data_termino,
                           pagination_args=pagination_args, 
                           sorting_args=sorting_args)

@app.route('/new_ferias', methods=['GET', 'POST'])
@login_required
@role_required(module='ferias', action='can_create')
def new_ferias():
    args = request.args.to_dict()
    conn = get_db_connection()
    if request.method == 'POST':
        form = request.form
        conn.execute('INSERT INTO ferias (funcionario, admissao, contrato, ano, data_inicio, data_termino, obs) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (form['funcionario'], form['admissao'], form['contrato'], form['ano'], form['data_inicio'], form['data_termino'], form['obs']))
        conn.commit()
        conn.close()
        flash('Novo plano de férias criado com sucesso!', 'success')
        return redirect(url_for('ferias'))
    tecnicos = conn.execute('SELECT nome, contrato FROM tecnicos ORDER BY nome').fetchall()
    conn.close()
    return render_template('new_ferias.html', tecnicos=tecnicos, args=args)

@app.route('/edit_ferias/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(module='ferias', action='can_edit')
def edit_ferias(id):
    args = request.args.to_dict()
    conn = get_db_connection()
    ferias_item = conn.execute('SELECT * FROM ferias WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        form = request.form
        conn.execute('UPDATE ferias SET funcionario=?, admissao=?, contrato=?, ano=?, data_inicio=?, data_termino=?, obs=? WHERE id=?',
                     (form['funcionario'], form['admissao'], form['contrato'], form['ano'], form['data_inicio'], form['data_termino'], form['obs'], id))
        conn.commit()
        conn.close()
        flash('Plano de férias atualizado com sucesso!', 'success')
        return redirect(url_for('ferias'))
    tecnicos = conn.execute('SELECT nome, contrato FROM tecnicos ORDER BY nome').fetchall()
    conn.close()
    return render_template('edit_ferias.html', ferias_item=ferias_item, tecnicos=tecnicos, args=args)

@app.route('/delete_ferias/<int:id>', methods=['POST'])
@login_required
@role_required(module='ferias', action='can_delete')
def delete_ferias(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM ferias WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Plano de férias excluído com sucesso!', 'success')
    return redirect(url_for('ferias'))

# --- MÓDULO DE AGENDA ---
@app.route('/agenda')
@login_required
@role_required(module='agenda', action='can_read')
def agenda():
    return render_template('agenda.html')

@app.route('/new_agenda', methods=['GET', 'POST'])
@login_required
@role_required(module='agenda', action='can_create')
def new_agenda():
    conn = get_db_connection()
    if request.method == 'POST':
        form = request.form
        conn.execute('INSERT INTO agenda (cliente, tecnico, sistema, data_agendamento, horario_agendamento, motivo, descricao, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (form['cliente'], form['tecnico'], form['sistema'], form['data_agendamento'], form['horario_agendamento'], form['motivo'], form['descricao'], form['status']))
        conn.commit()
        conn.close()
        return redirect(url_for('agenda'))
    pre_selected_date = request.args.get('data_agendamento', '')
    clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
    tecnicos = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    conn.close()
    return render_template('new_agenda.html', clientes=clientes, tecnicos=tecnicos, sistemas=sistemas, pre_selected_date=pre_selected_date)

@app.route('/edit_agenda/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(module='agenda', action='can_edit')
def edit_agenda(id):
    conn = get_db_connection()
    agendamento = conn.execute('SELECT * FROM agenda WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        form = request.form
        conn.execute('UPDATE agenda SET cliente=?, tecnico=?, sistema=?, data_agendamento=?, horario_agendamento=?, motivo=?, descricao=?, status=? WHERE id=?',
                     (form['cliente'], form['tecnico'], form['sistema'], form['data_agendamento'], form['horario_agendamento'], form['motivo'], form['descricao'], form['status'], id))
        conn.commit()
        conn.close()
        return redirect(url_for('agenda'))
    clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
    tecnicos = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    conn.close()
    return render_template('edit_agenda.html', agendamento=agendamento, clientes=clientes, tecnicos=tecnicos, sistemas=sistemas)

@app.route('/delete_agenda/<int:id>', methods=['POST'])
@login_required
@role_required(module='agenda', action='can_delete')
def delete_agenda(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM agenda WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Agendamento excluído com sucesso!', 'success')
    return redirect(url_for('agenda'))

# --- MÓDULO DE PRESTAÇÃO DE CONTAS ---
@app.route('/prestacao_contas')
@login_required
@role_required(module='prestacao_contas', action='can_read')
def prestacao_contas():
    conn = get_db_connection()
    per_page = 20
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'id', type=str)
    order = request.args.get('order', 'desc', type=str)
    search_cliente = request.args.get('search_cliente', '', type=str)
    search_sistema = request.args.get('search_sistema', '', type=str)
    search_responsavel = request.args.get('search_responsavel', '', type=str)
    search_status = request.args.get('search_status', '', type=str)
    search_modulo = request.args.get('search_modulo', '', type=str)
    search_competencia = request.args.get('search_competencia', '', type=str)
    search_observacao = request.args.get('search_observacao', '', type=str)
    search_atualizado_por = request.args.get('search_atualizado_por', '', type=str)

    allowed_sort_columns = ['id', 'cliente', 'sistema', 'responsavel', 'modulo', 'competencia', 'status', 'observacao', 'atualizado_por']
    if sort_by not in allowed_sort_columns: sort_by = 'id'
    if order.lower() not in ['asc', 'desc']: order = 'desc'

    offset = (page - 1) * per_page
    base_query = "FROM prestacao_contas WHERE 1=1"
    params = []
    if search_cliente:
        base_query += " AND cliente LIKE ?"
        params.append(f"%{search_cliente}%")
    if search_sistema:
        base_query += " AND sistema LIKE ?"
        params.append(f"%{search_sistema}%")
    if search_responsavel:
        base_query += " AND responsavel LIKE ?"
        params.append(f"%{search_responsavel}%")
    if search_status:
        base_query += " AND status = ?"
        params.append(search_status)
    if search_modulo:
        base_query += " AND modulo LIKE ?"
        params.append(f"%{search_modulo}%")
    if search_competencia:
        base_query += " AND competencia LIKE ?"
        params.append(f"%{search_competencia}%")
    if search_observacao:
        base_query += " AND observacao LIKE ?"
        params.append(f"%{search_observacao}%")
    if search_atualizado_por:
        base_query += " AND atualizado_por LIKE ?"
        params.append(f"%{search_atualizado_por}%")
    total_query = "SELECT COUNT(id) " + base_query
    total_results = conn.execute(total_query, tuple(params)).fetchone()[0]
    total_pages = (total_results + per_page - 1) // per_page
    data_query = f"SELECT * {base_query} ORDER BY {sort_by} {order} LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    dados = conn.execute(data_query, tuple(params)).fetchall()
    status_counts_data = conn.execute("SELECT status, COUNT(id) as count FROM prestacao_contas GROUP BY status").fetchall()
    status_counts = {row['status']: row['count'] for row in status_counts_data}
    clientes_filtro = [row['cliente'] for row in conn.execute('SELECT DISTINCT cliente FROM prestacao_contas ORDER BY cliente').fetchall()]
    sistemas_filtro = [row['sistema'] for row in conn.execute('SELECT DISTINCT sistema FROM prestacao_contas ORDER BY sistema').fetchall()]
    responsaveis_filtro = [row['responsavel'] for row in conn.execute('SELECT DISTINCT responsavel FROM prestacao_contas ORDER BY responsavel').fetchall()]
    conn.close()
    pagination_args = request.args.to_dict()
    if 'page' in pagination_args: del pagination_args['page']
    sorting_args = request.args.to_dict()
    if 'sort_by' in sorting_args: del sorting_args['sort_by']
    if 'order' in sorting_args: del sorting_args['order']
    return render_template('prestacao_contas.html', dados=dados, page=page, total_pages=total_pages,
                           sort_by=sort_by, order=order, status_counts=status_counts,
                           search_cliente=search_cliente, search_sistema=search_sistema,
                           search_responsavel=search_responsavel, search_status=search_status,
                           search_modulo=search_modulo, search_competencia=search_competencia,
                           search_observacao=search_observacao, search_atualizado_por=search_atualizado_por,
                           clientes_filtro=clientes_filtro, sistemas_filtro=sistemas_filtro,
                           responsaveis_filtro=responsaveis_filtro,
                           pagination_args=pagination_args, sorting_args=sorting_args)

@app.route('/new_prestacao', methods=['GET', 'POST'])
@login_required
@role_required(module='prestacao_contas', action='can_create')
def new_prestacao():
    args = request.args.to_dict()
    if request.method == 'POST':
        conn = get_db_connection()
        form = request.form
        atualizado_por = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} por {session.get('user_name', 'Desconhecido')}"
        conn.execute('INSERT INTO prestacao_contas (cliente, sistema, responsavel, modulo, competencia, status, observacao, atualizado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (form['cliente'], form['sistema'], form['responsavel'], form['modulo'], form['competencia'], form['status'], form['observacao'], atualizado_por))
        conn.commit()
        conn.close()
        flash('Registo criado com sucesso!', 'success')
        redirect_args = {}
        valid_state_keys = ['search_cliente', 'search_sistema', 'search_responsavel', 'search_status', 'search_modulo', 'search_competencia', 'search_observacao', 'search_atualizado_por', 'page', 'sort_by', 'order']
        for key in valid_state_keys:
            value = request.form.get(key)
            if value: redirect_args[key] = value
        return redirect(url_for('prestacao_contas', **redirect_args))
    conn = get_db_connection()
    clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    conn.close()
    return render_template('new_prestacao.html', clientes=clientes, sistemas=sistemas, responsaveis=responsaveis, args=args)

@app.route('/edit_prestacao/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(module='prestacao_contas', action='can_edit')
def edit_prestacao(id):
    args = request.args.to_dict()
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM prestacao_contas WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        form = request.form
        atualizado_por = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} por {session.get('user_name', 'Desconhecido')}"
        conn.execute('UPDATE prestacao_contas SET cliente=?, sistema=?, responsavel=?, modulo=?, competencia=?, status=?, observacao=?, atualizado_por=? WHERE id=?',
            (form['cliente'], form['sistema'], form['responsavel'], form['modulo'], form['competencia'], form['status'], form['observacao'], atualizado_por, id))
        conn.commit()
        conn.close()
        flash('Registo atualizado com sucesso!', 'success')
        redirect_args = {}
        valid_state_keys = ['search_cliente', 'search_sistema', 'search_responsavel', 'search_status', 'search_modulo', 'search_competencia', 'search_observacao', 'search_atualizado_por', 'page', 'sort_by', 'order']
        for key in valid_state_keys:
            value = request.form.get(key)
            if value: redirect_args[key] = value
        return redirect(url_for('prestacao_contas', **redirect_args))
    clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    conn.close()
    return render_template('edit_prestacao.html', item=item, clientes=clientes, sistemas=sistemas, responsaveis=responsaveis, args=args)

@app.route('/delete_prestacao/<int:id>', methods=['POST'])
@login_required
@role_required(module='prestacao_contas', action='can_delete')
def delete_prestacao(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM prestacao_contas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Registo excluído com sucesso!', 'success')
    redirect_args = {}
    valid_state_keys = ['search_cliente', 'search_sistema', 'search_responsavel', 'search_status', 'search_modulo', 'search_competencia', 'search_observacao', 'search_atualizado_por', 'page', 'sort_by', 'order']
    for key in valid_state_keys:
        value = request.form.get(key)
        if value: redirect_args[key] = value
    return redirect(url_for('prestacao_contas', **redirect_args))

# --- GESTÃO DE USUÁRIOS (Admin) ---
@app.route('/usuarios')
@login_required
@role_required(module='admin_only', action='can_read')
def usuarios():
    conn = get_db_connection()
    users_data = conn.execute('SELECT id, nome, email, role FROM usuarios').fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=users_data)

@app.route('/new_usuario', methods=['GET', 'POST'])
@login_required
@role_required(module='admin_only', action='can_create')
def new_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        role = request.form['role']

        # --- CORREÇÃO APLICADA AQUI ---
        # Define um valor padrão para 'nivel_acesso' com base no 'role'
        niveis_acesso = {
            'admin': 'Admin',
            'coordenacao': 'Usuario',
            'tecnico': 'Usuario'
        }
        nivel_acesso = niveis_acesso.get(role, 'Usuario') # Padrão para 'Usuario'
        # --- FIM DA CORREÇÃO ---

        conn = get_db_connection()
        try:
            # Adiciona o 'nivel_acesso' ao INSERT
            conn.execute('INSERT INTO usuarios (nome, email, senha, role, nivel_acesso) VALUES (?, ?, ?, ?, ?)',
                         (nome, email, generate_password_hash(senha), role, nivel_acesso))
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
@role_required(module='admin_only', action='can_edit')
def edit_usuario(id):
    conn = get_db_connection()
    usuario = conn.execute('SELECT id, nome, email, role FROM usuarios WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        nome, email, role, senha = request.form['nome'], request.form['email'], request.form['role'], request.form.get('senha')
        try:
            if senha:
                conn.execute('UPDATE usuarios SET nome=?, email=?, role=?, senha=? WHERE id=?', (nome, email, role, generate_password_hash(senha), id))
            else:
                conn.execute('UPDATE usuarios SET nome=?, email=?, role=? WHERE id=?', (nome, email, role, id))
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
@role_required(module='admin_only', action='can_delete')
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

# --- MÓDULO DE MATRIZ DE RESPONSABILIDADES ---
# ALTERAÇÃO APLICADA AQUI
@app.route('/matriz')
@login_required
@role_required(module='matriz', action='can_read')
def matriz_responsabilidades():
    conn = get_db_connection()
    view = request.args.get('view', 'list')
    if view == 'matrix':
        all_clientes = conn.execute("SELECT municipio || ' - ' || orgao as nome FROM clientes ORDER BY nome").fetchall()
        sistemas_a_excluir = ('Compras, Licitações e Contratos', 'Frotas', 'Patrimônio', 'Almoxarifado', 'Nota Fiscal de Serviços Eletrônicos', 'Portal da Transparência', 'Portal do Servidor')
        placeholders = ','.join('?' for _ in sistemas_a_excluir)
        query_sistemas = f"SELECT nome FROM sistemas WHERE nome NOT IN ({placeholders}) ORDER BY nome"
        all_sistemas = conn.execute(query_sistemas, sistemas_a_excluir).fetchall()
        registos = conn.execute("SELECT cliente, sistema, responsavel1, responsavel2 FROM matriz_responsabilidades").fetchall()
        matriz_data = {}
        for reg in registos:
            if reg['cliente'] not in matriz_data: matriz_data[reg['cliente']] = {}
            responsaveis_str = reg['responsavel1']
            if reg['responsavel2']: responsaveis_str += f" / {reg['responsavel2']}"
            matriz_data[reg['cliente']][reg['sistema']] = responsaveis_str
        conn.close()
        return render_template('matriz_responsabilidades.html', view=view, all_clientes=all_clientes, all_sistemas=all_sistemas, matriz_data=matriz_data)
    else:
        search_cliente = request.args.get('search_cliente', '', type=str)
        search_sistema = request.args.get('search_sistema', '', type=str)
        search_responsavel = request.args.get('search_responsavel', '', type=str)
        base_query = "SELECT * FROM matriz_responsabilidades WHERE 1=1"
        params = []
        if search_cliente:
            base_query += " AND cliente = ?"
            params.append(search_cliente)
        if search_sistema:
            base_query += " AND sistema = ?"
            params.append(search_sistema)
        if search_responsavel:
            base_query += " AND (responsavel1 = ? OR responsavel2 = ?)"
            params.extend([search_responsavel, search_responsavel])
        base_query += " ORDER BY cliente, sistema"
        registos = conn.execute(base_query, tuple(params)).fetchall()
        clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
        sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
        responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
        conn.close()
        return render_template('matriz_responsabilidades.html', view=view, registos=registos, clientes=clientes, sistemas=sistemas, responsaveis=responsaveis, search_cliente=search_cliente, search_sistema=search_sistema, search_responsavel=search_responsavel)

# ALTERAÇÃO APLICADA AQUI
@app.route('/matriz/new', methods=['GET', 'POST'])
@login_required
@role_required(module='matriz', action='can_create')
def new_matriz_responsabilidade():
    if request.method == 'POST':
        form = request.form
        conn = get_db_connection()
        conn.execute('INSERT INTO matriz_responsabilidades (cliente, sistema, responsavel1, responsavel2, observacoes) VALUES (?, ?, ?, ?, ?)',
                     (form['cliente'], form['sistema'], form['responsavel1'], form.get('responsavel2'), form['observacoes']))
        conn.commit()
        conn.close()
        flash('Registo de responsabilidade criado com sucesso!', 'success')
        return redirect(url_for('matriz_responsabilidades'))
    conn = get_db_connection()
    clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    conn.close()
    return render_template('new_matriz.html', clientes=clientes, sistemas=sistemas, responsaveis=responsaveis)

# ALTERAÇÃO APLICADA AQUI
@app.route('/matriz/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(module='matriz', action='can_edit')
def edit_matriz_responsabilidade(id):
    conn = get_db_connection()
    registo = conn.execute('SELECT * FROM matriz_responsabilidades WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        form = request.form
        conn.execute('UPDATE matriz_responsabilidades SET cliente=?, sistema=?, responsavel1=?, responsavel2=?, observacoes=? WHERE id=?',
                     (form['cliente'], form['sistema'], form['responsavel1'], form.get('responsavel2'), form['observacoes'], id))
        conn.commit()
        conn.close()
        flash('Registo de responsabilidade atualizado com sucesso!', 'success')
        return redirect(url_for('matriz_responsabilidades'))
    clientes = [f"{c['municipio']} - {c['orgao']}" for c in conn.execute('SELECT municipio, orgao FROM clientes ORDER BY municipio').fetchall()]
    sistemas = [row['nome'] for row in conn.execute('SELECT nome FROM sistemas ORDER BY nome').fetchall()]
    responsaveis = [row['nome'] for row in conn.execute('SELECT nome FROM tecnicos ORDER BY nome').fetchall()]
    conn.close()
    return render_template('edit_matriz.html', registo=registo, clientes=clientes, sistemas=sistemas, responsaveis=responsaveis)

# ALTERAÇÃO APLICADA AQUI
@app.route('/matriz/delete/<int:id>', methods=['POST'])
@login_required
@role_required(module='matriz', action='can_delete')
def delete_matriz_responsabilidade(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM matriz_responsabilidades WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Registo de responsabilidade excluído com sucesso.', 'success')
    return redirect(url_for('matriz_responsabilidades'))

# --- ROTA DE API PARA O CALENDÁRIO ---
@app.route('/api/agendamentos')
@login_required
def api_agendamentos():
    conn = get_db_connection()
    agendamentos_db = conn.execute('SELECT * FROM agenda').fetchall()
    conn.close()
    
    color_map = {
        'Planejada': '#3498db',                            # Azul
        'Realizada': '#2ecc71',                            # Verde
        'Cancelada': '#95a5a6',                            # Cinza
        'Aguardando Confirmação do Cliente': '#f1c40f'     # Amarelo
    }
    
    eventos = []
    for agendamento in agendamentos_db:
        start_datetime = agendamento['data_agendamento']
        
        horario_limpo = None
        raw_horario = agendamento['horario_agendamento']
        if raw_horario:
            # Usa expressão regular para encontrar um padrão de hora (ex: 14:00 ou 9:30)
            match = re.search(r'\d{1,2}:\d{2}', raw_horario)
            if match:
                horario_limpo = match.group(0)
                start_datetime += f"T{horario_limpo}"

        # --- ALTERAÇÃO APLICADA AQUI: Construção do título completo ---
        title_parts = []
        if horario_limpo:
            title_parts.append(f"{horario_limpo} -")
        
        title_parts.append(f"{agendamento['cliente']} ({agendamento['tecnico']})")
        
        if agendamento['motivo']:
            title_parts.append(f"- {agendamento['motivo']}")
            
        titulo_completo = " ".join(title_parts)
        # --- FIM DA ALTERAÇÃO ---
        
        event_color = color_map.get(agendamento['status'], '#808080')
            
        eventos.append({
            'id': agendamento['id'],
            'title': titulo_completo, # Usa o novo título completo
            'start': start_datetime,
            'backgroundColor': event_color,
            'borderColor': event_color,
            'textColor': '#ffffff',
            'extendedProps': {
                'motivo': agendamento['motivo'],
                'descricao': agendamento['descricao'],
                'status': agendamento['status'],
                'cliente': agendamento['cliente'],
                'tecnico': agendamento['tecnico'],
                'horario': horario_limpo
            }
        })
        
    return jsonify(eventos)
# --- ROTA TEMPORÁRIA PARA CORREÇÃO DO BANCO DE DADOS ---
@app.route('/force_db_fix')
@login_required
def force_db_fix():
    print("--- INICIANDO CORREÇÃO MANUAL DO BANCO DE DADOS ---")
    try:
        # Re-executa as migrações importantes
        migrate_permissions_for_create()
        migrate_pendencias_add_prioridade() 
        migrate_pendencias_add_unique_protocolo()
        migrate_tarefas_add_predecessoras()
        flash('A verificação e correção da estrutura do banco de dados foi executada com sucesso!', 'success')
        print("--- CORREÇÃO MANUAL DO BANCO DE DADOS CONCLUÍDA ---")
    except Exception as e:
        flash(f'Ocorreu um erro durante a correção da estrutura: {e}', 'danger')
        print(f"--- ERRO NA CORREÇÃO MANUAL DA ESTRUTURA: {e} ---")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)