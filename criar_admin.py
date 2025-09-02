import sqlite3
from werkzeug.security import generate_password_hash

# --- CONFIGURE SEU ADMIN AQUI ---
ADMIN_NOME = "Laura"
ADMIN_EMAIL = "laura.costa@ibtechti.com.br"
ADMIN_SENHA = "Emanuel2037*" # Troque por uma senha segura
# -----------------------------------

# Gera o hash da senha
hashed_senha = generate_password_hash(ADMIN_SENHA)

# Conecta ao banco de dados
conn = sqlite3.connect('/tmp/database.db')
cursor = conn.cursor()

try:
    # Insere o novo usuário admin na tabela
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, nivel_acesso) VALUES (?, ?, ?, ?)",
        (ADMIN_NOME, ADMIN_EMAIL, hashed_senha, 'Admin')
    )
    conn.commit()
    print(f"Usuário '{ADMIN_EMAIL}' criado com sucesso!")

except sqlite3.IntegrityError:
    print(f"Erro: O usuário com email '{ADMIN_EMAIL}' já existe.")

finally:
    # Fecha a conexão
    conn.close()