from datetime import datetime, timedelta
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

# Conexão com o SQLite
conexao = sqlite3.connect("biblioteca.db", check_same_thread=False)
cursor = conexao.cursor()

# Criar tabelas necessárias (Funcionários, Livros e Empréstimos)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL,
        senha TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS livros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        autor TEXT NOT NULL,
        isbn TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'Disponível'
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS emprestimos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        livro_id INTEGER,
        nome_usuario TEXT NOT NULL,
        data_emprestimo TEXT NOT NULL,
        data_devolucao TEXT NOT NULL,
        FOREIGN KEY (livro_id) REFERENCES livros (id)
    )
""")
conexao.commit()

print("Banco de dados configurado com sucesso!")


# --- LOGIN (Parte da sua colega) ---
@app.route("/", methods=["GET", "POST"])
def inicio():
  if request.method == "POST":
    usuario = request.form["usuario"]
    senha = request.form["senha"]
    cursor.execute(
        "SELECT * FROM funcionarios WHERE usuario = ? AND senha = ?",
        (usuario, senha),
    )
    funcionario = cursor.fetchone()

    if funcionario:
      return render_template("sistema.html")
    else:
      return "Usuário ou senha incorretos."
  return render_template("index.html")


# --- CADASTRO DE LIVROS (Sua parte anterior) ---
@app.route("/cadastro_livro", methods=["GET", "POST"])
def cadastro_livro():
  erro = None
  sucesso = None

  if request.method == "POST":
    titulo = request.form.get("titulo")
    autor = request.form.get("autor")
    isbn = request.form.get("isbn").strip()

    if not isbn.isdigit() or len(isbn) != 13:
      erro = "O ISBN deve conter exatamente 13 dígitos numéricos."
    else:
      try:
        cursor.execute(
            "INSERT INTO livros (titulo, autor, isbn, status) VALUES (?, ?,"
            " ?, 'Disponível')",
            (titulo, autor, isbn),
        )
        conexao.commit()
        sucesso = "Livro cadastrado com sucesso!"
      except sqlite3.IntegrityError:
        erro = "Este ISBN já está cadastrado no sistema (ISBN duplicado)."

  return render_template("cadastro_livro.html", erro=erro, sucesso=sucesso)


# --- REGISTRO DE EMPRÉSTIMO (Nova parte) ---
@app.route("/emprestimo", methods=["GET", "POST"])
def realizar_emprestimo():
  erro = None
  sucesso = None

  if request.method == "POST":
    livro_id = request.form.get("livro_id")
    nome_usuario = request.form.get("nome_usuario")

    # 1. Verifica se o livro realmente está com status 'Disponível'
    cursor.execute("SELECT status FROM livros WHERE id = ?", (livro_id,))
    livro = cursor.fetchone()

    if not livro:
      erro = "Livro não encontrado."
    elif livro[0] != "Disponível":
      erro = "Este livro não está disponível para empréstimo no momento."
    else:
      # 2. Calcula as datas automaticamente em Python
      data_atual = datetime.now()
      data_emprestimo_str = data_atual.strftime("%Y-%m-%d")

      # Adiciona exatamente 7 dias corridos
      data_devolucao_obj = data_atual + timedelta(days=7)
      data_devolucao_str = data_devolucao_obj.strftime("%Y-%m-%d")

      # 3. Registra o empréstimo na tabela e muda o status do livro para 'Emprestado'
      cursor.execute(
          "INSERT INTO emprestimos (livro_id, nome_usuario, data_emprestimo,"
          " data_devolucao) VALUES (?, ?, ?, ?)",
          (livro_id, nome_usuario, data_emprestimo_str, data_devolucao_str),
      )

      cursor.execute(
          "UPDATE livros SET status = 'Emprestado' WHERE id = ?", (livro_id,)
      )
      conexao.commit()

      sucesso = (
          f"Empréstimo realizado com sucesso! Data limite para devolução:"
          f" {data_devolucao_str}"
      )

# Busca apenas os livros que estão disponíveis para aparecer no select do HTML
  cursor.execute("SELECT id, titulo, autor FROM livros WHERE status = 'Disponível'")
  livros_disponiveis = cursor.fetchall()

  return render_template(
      "emprestimo.html",
      livros=livros_disponiveis,
      erro=erro,
      sucesso=sucesso,
  )


if __name__ == "__main__":
  app.run(debug=True)