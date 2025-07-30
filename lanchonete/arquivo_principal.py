
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Configuração do banco de dados
DATABASE = 'lanchonete.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            sobrenome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
        ''')
        
        # Tabela de itens do cardápio
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cardapio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            preco REAL NOT NULL,
            imagem TEXT NOT NULL,
            tags TEXT
        )
        ''')
        
        # Inserir dados iniciais do cardápio
        cardapio_inicial = [
            # Combos
            ('Combos', 'Combo Mega Burger', 'Hambúrguer artesanal 180g, queijo cheddar, bacon, batata frita média e refrigerante 350ml', 29.90, 'combo1.jpg', 'combo,novo'),
            # Lanches
            ('Lanches', 'X-Tudo Completo', 'Pão brioche, 2 carnes 180g, queijo, presunto, ovo, bacon, alface, tomate, milho, ervilha, batata palha e maionese', 18.90, 'xtudo.jpg', ''),
            # ... outros itens
        ]
        
        cursor.executemany('''
        INSERT INTO cardapio (categoria, nome, descricao, preco, imagem, tags)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', cardapio_inicial)
        
        conn.commit()
        conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('cardapio'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['senha'], senha):
            session['user_id'] = user['id']
            session['user_nome'] = user['nome']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('cardapio'))
        else:
            flash('E-mail ou senha incorretos', 'danger')
    
    return render_template('login.html')

@app.route('/visitante')
def visitante():
    session['visitante'] = True
    return redirect(url_for('cardapio'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        sobrenome = request.form['sobrenome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nome, sobrenome, email, senha) VALUES (?, ?, ?, ?)',
                         (nome, sobrenome, email, senha))
            conn.commit()
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('E-mail já cadastrado', 'danger')
        finally:
            conn.close()
    
    return render_template('cadastro.html')

@app.route('/cardapio')
def cardapio():
    if 'user_id' not in session and 'visitante' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    categorias = conn.execute('SELECT DISTINCT categoria FROM cardapio').fetchall()
    
    cardapio_itens = {}
    for categoria in categorias:
        itens = conn.execute('SELECT * FROM cardapio WHERE categoria = ?', (categoria['categoria'],)).fetchall()
        cardapio_itens[categoria['categoria']] = itens
    
    conn.close()
    
    return render_template('cardapio.html', 
                         cardapio=cardapio_itens,
                         usuario=session.get('user_nome'),
                         visitante='visitante' in session)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)