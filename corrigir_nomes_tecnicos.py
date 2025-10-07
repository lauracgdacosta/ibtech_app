import sqlite3

# Caminho para o seu banco de dados
DATABASE_PATH = '/tmp/database.db'

def corrigir_nomes():
    print("--- Iniciando a correção dos nomes dos técnicos ---")
    try:
        # Conecta-se ao banco de dados
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Seleciona todos os técnicos
        cursor.execute("SELECT id, nome FROM tecnicos")
        tecnicos = cursor.fetchall()

        if not tecnicos:
            print("Nenhum técnico encontrado para corrigir.")
            return

        print(f"Encontrados {len(tecnicos)} técnicos. Processando...")

        # 2. Itera sobre cada técnico, corrige o nome e prepara para atualizar
        for tecnico in tecnicos:
            id_tecnico = tecnico['id']
            nome_antigo = tecnico['nome']
            
            # Converte o nome para o formato de título (Ex: "NOME COMPLETO" -> "Nome Completo")
            nome_corrigido = nome_antigo.title()

            if nome_antigo != nome_corrigido:
                print(f"ID {id_tecnico}: Alterando '{nome_antigo}' para '{nome_corrigido}'")
                # 3. Executa a atualização no banco de dados
                cursor.execute("UPDATE tecnicos SET nome = ? WHERE id = ?", (nome_corrigido, id_tecnico))
            else:
                print(f"ID {id_tecnico}: Nome '{nome_antigo}' já está no formato correto. Nenhuma alteração necessária.")

        # 4. Salva (comita) todas as alterações no banco de dados
        conn.commit()
        print("\nSUCESSO! Todos os nomes foram corrigidos e salvos no banco de dados.")

    except sqlite3.Error as e:
        print(f"\nERRO: Ocorreu um erro ao aceder ao banco de dados: {e}")
    finally:
        if conn:
            conn.close()
        print("--- Fim do script ---")

# Executa a função
if __name__ == '__main__':
    corrigir_nomes()