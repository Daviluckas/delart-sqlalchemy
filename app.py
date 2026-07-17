import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_required, login_user, logout_user,
    current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'delart-estetica-automotiva-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'delart.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# modelos

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    senha = db.Column(db.String(200), nullable=False)

    lavagens = db.relationship('Lavagem', backref='usuario', lazy=True)
    polimentos = db.relationship('Polimento', backref='usuario', lazy=True)
    restauracoes = db.relationship('Restauracao', backref='usuario', lazy=True)


class Lavagem(db.Model):
    __tablename__ = 'lavagens'
    id = db.Column(db.Integer, primary_key=True)
    veiculo = db.Column(db.String(100), nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    data_agendada = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), default='Pendente')
    observacoes = db.Column(db.Text, default='')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)


class Polimento(db.Model):
    __tablename__ = 'polimentos'
    id = db.Column(db.Integer, primary_key=True)
    veiculo = db.Column(db.String(100), nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    data_agendada = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), default='Pendente')
    observacoes = db.Column(db.Text, default='')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)


class Restauracao(db.Model):
    __tablename__ = 'restauracoes'
    id = db.Column(db.Integer, primary_key=True)
    veiculo = db.Column(db.String(100), nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    data_agendada = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), default='Pendente')
    observacoes = db.Column(db.Text, default='')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)


# login

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# rotas públicas

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('painel'))
    return render_template('index.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']

        if Usuario.query.filter_by(nome=nome).first():
            flash('Nome de usuário já existe.', 'erro')
            return redirect(url_for('registro'))

        novo = Usuario(nome=nome, senha=generate_password_hash(senha))
        db.session.add(novo)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Faça login.', 'sucesso')
        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']

        usuario = Usuario.query.filter_by(nome=nome).first()
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            return redirect(url_for('painel'))
        flash('Usuário ou senha inválidos.', 'erro')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sessão.', 'sucesso')
    return redirect(url_for('login'))


# painel

@app.route('/painel')
@login_required
def painel():
    return render_template('painel.html', usuario=current_user)


# crud lavagem

@app.route('/lavagens')
@login_required
def lavagens_listar():
    busca = request.args.get('q', '', type=str)
    query = Lavagem.query.filter_by(usuario_id=current_user.id)
    if busca:
        query = query.filter(Lavagem.veiculo.contains(busca))
    lavagens = query.order_by(Lavagem.data_agendada).all()
    return render_template('lavagens/listar.html', lavagens=lavagens, q=busca)


@app.route('/lavagens/nova', methods=['GET', 'POST'])
@login_required
def lavagens_nova():
    if request.method == 'POST':
        l = Lavagem(
            veiculo=request.form['veiculo'],
            placa=request.form['placa'],
            tipo=request.form['tipo'],
            data_agendada=request.form['data_agendada'],
            status=request.form.get('status', 'Pendente'),
            observacoes=request.form.get('observacoes', ''),
            usuario_id=current_user.id
        )
        db.session.add(l)
        db.session.commit()
        flash('Lavagem agendada com sucesso!', 'sucesso')
        return redirect(url_for('lavagens_listar'))
    return render_template('lavagens/form.html', acao='Nova', lavagem=None)


@app.route('/lavagens/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def lavagens_editar(id):
    lavagem = Lavagem.query.get_or_404(id)
    if lavagem.usuario_id != current_user.id:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('lavagens_listar'))
    if request.method == 'POST':
        lavagem.veiculo = request.form['veiculo']
        lavagem.placa = request.form['placa']
        lavagem.tipo = request.form['tipo']
        lavagem.data_agendada = request.form['data_agendada']
        lavagem.status = request.form.get('status', 'Pendente')
        lavagem.observacoes = request.form.get('observacoes', '')
        db.session.commit()
        flash('Lavagem atualizada!', 'sucesso')
        return redirect(url_for('lavagens_listar'))
    return render_template('lavagens/form.html', acao='Editar', lavagem=lavagem)


@app.route('/lavagens/remover/<int:id>', methods=['POST'])
@login_required
def lavagens_remover(id):
    lavagem = Lavagem.query.get_or_404(id)
    if lavagem.usuario_id != current_user.id:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('lavagens_listar'))
    db.session.delete(lavagem)
    db.session.commit()
    flash('Lavagem removida.', 'sucesso')
    return redirect(url_for('lavagens_listar'))


# crud polimento

@app.route('/polimentos')
@login_required
def polimentos_listar():
    busca = request.args.get('q', '', type=str)
    query = Polimento.query.filter_by(usuario_id=current_user.id)
    if busca:
        query = query.filter(Polimento.veiculo.contains(busca))
    polimentos = query.order_by(Polimento.data_agendada).all()
    return render_template('polimentos/listar.html', polimentos=polimentos, q=busca)


@app.route('/polimentos/novo', methods=['GET', 'POST'])
@login_required
def polimentos_novo():
    if request.method == 'POST':
        p = Polimento(
            veiculo=request.form['veiculo'],
            placa=request.form['placa'],
            tipo=request.form['tipo'],
            data_agendada=request.form['data_agendada'],
            status=request.form.get('status', 'Pendente'),
            observacoes=request.form.get('observacoes', ''),
            usuario_id=current_user.id
        )
        db.session.add(p)
        db.session.commit()
        flash('Polimento agendado com sucesso!', 'sucesso')
        return redirect(url_for('polimentos_listar'))
    return render_template('polimentos/form.html', acao='Novo', polimento=None)


@app.route('/polimentos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def polimentos_editar(id):
    polimento = Polimento.query.get_or_404(id)
    if polimento.usuario_id != current_user.id:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('polimentos_listar'))
    if request.method == 'POST':
        polimento.veiculo = request.form['veiculo']
        polimento.placa = request.form['placa']
        polimento.tipo = request.form['tipo']
        polimento.data_agendada = request.form['data_agendada']
        polimento.status = request.form.get('status', 'Pendente')
        polimento.observacoes = request.form.get('observacoes', '')
        db.session.commit()
        flash('Polimento atualizado!', 'sucesso')
        return redirect(url_for('polimentos_listar'))
    return render_template('polimentos/form.html', acao='Editar', polimento=polimento)


@app.route('/polimentos/remover/<int:id>', methods=['POST'])
@login_required
def polimentos_remover(id):
    polimento = Polimento.query.get_or_404(id)
    if polimento.usuario_id != current_user.id:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('polimentos_listar'))
    db.session.delete(polimento)
    db.session.commit()
    flash('Polimento removido.', 'sucesso')
    return redirect(url_for('polimentos_listar'))


# crud restauração

@app.route('/restauracoes')
@login_required
def restauracoes_listar():
    busca = request.args.get('q', '', type=str)
    query = Restauracao.query.filter_by(usuario_id=current_user.id)
    if busca:
        query = query.filter(Restauracao.veiculo.contains(busca))
    restauracoes = query.order_by(Restauracao.data_agendada).all()
    return render_template('restauracoes/listar.html', restauracoes=restauracoes, q=busca)


@app.route('/restauracoes/nova', methods=['GET', 'POST'])
@login_required
def restauracoes_nova():
    if request.method == 'POST':
        r = Restauracao(
            veiculo=request.form['veiculo'],
            placa=request.form['placa'],
            tipo=request.form['tipo'],
            data_agendada=request.form['data_agendada'],
            status=request.form.get('status', 'Pendente'),
            observacoes=request.form.get('observacoes', ''),
            usuario_id=current_user.id
        )
        db.session.add(r)
        db.session.commit()
        flash('Restauração agendada com sucesso!', 'sucesso')
        return redirect(url_for('restauracoes_listar'))
    return render_template('restauracoes/form.html', acao='Nova', restauracao=None)


@app.route('/restauracoes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def restauracoes_editar(id):
    restauracao = Restauracao.query.get_or_404(id)
    if restauracao.usuario_id != current_user.id:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('restauracoes_listar'))
    if request.method == 'POST':
        restauracao.veiculo = request.form['veiculo']
        restauracao.placa = request.form['placa']
        restauracao.tipo = request.form['tipo']
        restauracao.data_agendada = request.form['data_agendada']
        restauracao.status = request.form.get('status', 'Pendente')
        restauracao.observacoes = request.form.get('observacoes', '')
        db.session.commit()
        flash('Restauração atualizada!', 'sucesso')
        return redirect(url_for('restauracoes_listar'))
    return render_template('restauracoes/form.html', acao='Editar', restauracao=restauracao)


@app.route('/restauracoes/remover/<int:id>', methods=['POST'])
@login_required
def restauracoes_remover(id):
    restauracao = Restauracao.query.get_or_404(id)
    if restauracao.usuario_id != current_user.id:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('restauracoes_listar'))
    db.session.delete(restauracao)
    db.session.commit()
    flash('Restauração removida.', 'sucesso')
    return redirect(url_for('restauracoes_listar'))


# detalhar

@app.route('/lavagens/<int:id>')
@login_required
def lavagens_detalhes(id):
    l = Lavagem.query.get_or_404(id)
    if l.usuario_id != current_user.id:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('lavagens_listar'))
    return render_template('lavagens/detalhes.html', lavagem=l)


@app.route('/polimentos/<int:id>')
@login_required
def polimentos_detalhes(id):
    p = Polimento.query.get_or_404(id)
    if p.usuario_id != current_user.id:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('polimentos_listar'))
    return render_template('polimentos/detalhes.html', polimento=p)


@app.route('/restauracoes/<int:id>')
@login_required
def restauracoes_detalhes(id):
    r = Restauracao.query.get_or_404(id)
    if r.usuario_id != current_user.id:
        flash('Acesso negado.', 'erro')
        return redirect(url_for('restauracoes_listar'))
    return render_template('restauracoes/detalhes.html', restauracao=r)


# iniciar o projeto

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
