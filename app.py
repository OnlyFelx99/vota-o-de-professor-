from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import time

app = Flask(__name__)
app.secret_key = "segredo"  # Necessário para exibir mensagens de erro no frontend

# Função para conectar ao banco de dados
def connect_db():
    conn = sqlite3.connect('votacao.db')
    return conn

# Função para inicializar o banco de dados
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS votos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        pontos INTEGER NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS cooldowns (
                        nome TEXT PRIMARY KEY,
                        ultima_votacao INTEGER)''')

    conn.commit()
    conn.close()

# Rota para a página inicial
@app.route('/')
def index():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM votos')
    votos = cursor.fetchall()
    conn.close()
    return render_template('index.html', votos=votos)

# Rota para votar com cooldown de 1 hora
@app.route('/votar', methods=['POST'])
def votar():
    nome = request.form['nome']
    tempo_atual = int(time.time())  # Obtém o tempo atual em segundos

    # Lista de nomes válidos
    nomes_validos = ["Ricardo", "Paulo", "Maestrâ", "Juliana", "Márcio", "Theany", "Bruna"]

    if nome not in nomes_validos:
        flash("Nome inválido!", "error")
        return redirect(url_for('index'))

    conn = connect_db()
    cursor = conn.cursor()

    # Verificar se o professor já foi votado recentemente
    cursor.execute('SELECT ultima_votacao FROM cooldowns WHERE nome = ?', (nome,))
    resultado = cursor.fetchone()

    if resultado:
        ultima_votacao = resultado[0]
        tempo_restante = 3600 - (tempo_atual - ultima_votacao)  # 3600 segundos = 1 hora
        if tempo_restante > 0:
            flash(f"Você só pode votar em {nome} novamente em {tempo_restante // 60} minutos.", "error")
            conn.close()
            return redirect(url_for('index'))

    # Atualizar a votação no banco de dados
    cursor.execute('SELECT pontos FROM votos WHERE nome = ?', (nome,))
    resultado = cursor.fetchone()

    if resultado:
        pontos = resultado[0] + 1
        cursor.execute('UPDATE votos SET pontos = ? WHERE nome = ?', (pontos, nome))
    else:
        cursor.execute('INSERT INTO votos (nome, pontos) VALUES (?, ?)', (nome, 1))

    # Atualizar a tabela de cooldowns
    cursor.execute('REPLACE INTO cooldowns (nome, ultima_votacao) VALUES (?, ?)', (nome, tempo_atual))

    conn.commit()
    conn.close()

    flash(f"Voto registrado para {nome}!", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
