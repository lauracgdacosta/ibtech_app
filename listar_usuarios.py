import sqlite3

print("--- Listando usuários cadastrados no sistema ---")

try:
    conn = sqlite3.connect('/tmp/database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    usuarios = cursor.execute("SELECT id, nome, email, nivel_acesso FROM usuarios").fetchall()

    if not usuarios:
        print("\nNenhum usuário encontrado no banco de dados!")
        print("Execute o passo a passo de criação do primeiro usuário novamente.")
    else:
        print(f"\nTotal de usuários: {len(usuarios)}")
        for usuario in usuarios:
            print(f"  - ID: {usuario['id']}, Nome: {usuario['nome']}, Email: {usuario['email']}, Nível: {usuario['nivel_acesso']}")

except Exception as e:
    print(f"Ocorreu um erro ao tentar ler o banco de dados: {e}")

finally:
    if conn:
        conn.close()

print("\n--- Fim da listagem ---")