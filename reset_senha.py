import sqlite3
from werkzeug.security import generate_password_hash

# --- INFORME OS DADOS PARA RESETAR A SENHA ---

# Coloque aqui o email EXATO do usuário que você quer resetar
EMAIL_DO_USUARIO = "admin@ibtech.com" 

# Digite a NOVA senha que você deseja usar
NOVA_SENHA = "novaSenhaForte123"

# ---------------------------------------------

print(f"Tentando resetar a senha para o usuário: {EMAIL_DO_USUARIO}...")

# Gera o novo hash para a nova senha
novo_hash = generate_password_hash(NOVA_SENHA)

try:
    # Conecta ao banco de dados
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Executa o comando para atualizar a senha do usuário específico
    cursor.execute("UPDATE usuarios SET senha = ? WHERE email = ?", (novo_hash, EMAIL_DO_USUARIO))

    # Verifica se alguma linha foi de fato alterada
    if cursor.rowcount == 0:
        print("\nERRO: Nenhum usuário encontrado com este email.")
        print("Verifique se o email foi digitado corretamente em EMAIL_DO_USUARIO.")
    else:
        conn.commit()
        print("\nSUCESSO! A senha foi resetada.")
        print(f"Agora você pode logar com o email '{EMAIL_DO_USUARIO}' e a senha '{NOVA_SENHA}'.")

except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")

finally:
    if conn:
        conn.close()