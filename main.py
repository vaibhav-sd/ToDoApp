from flask import Flask, render_template, request, redirect, url_for, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key' 
db_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'todos.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class ToDoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    time = db.Column(db.String(50))
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"ToDoItem(id={self.id}, title={self.title}, completed={self.completed})"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_tables():
    db.create_all()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('get_todo_list'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        login_user(user)
        return redirect(url_for('get_todo_list'))
    return render_template('login.html', error='Invalid username or password')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/todos', methods=['GET'])
@login_required
def get_todo_list():
    todo_items = ToDoItem.query.filter_by(user_id=current_user.id).order_by(ToDoItem.completed)
    return render_template('todos.html', todo_items=todo_items)

@app.route('/todos/add', methods=['POST'])
@login_required
def add_todo():
    title = request.form['title']
    description = request.form['description']
    time = request.form['time']
    new_todo = ToDoItem(title=title, description=description, time=time, user_id=current_user.id)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for('get_todo_list'))

@app.route('/todos/<int:todo_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_todo(todo_id):
    todo = ToDoItem.query.get_or_404(todo_id)
    if request.method == 'POST':
        todo.title = request.form['title']
        todo.description = request.form['description']
        todo.time = request.form['time']
        db.session.commit()
        return redirect(url_for('get_todo_list'))
    return render_template('edit_todo.html', todo=todo)

@app.route('/todos/<int:todo_id>/delete', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todo = ToDoItem.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('get_todo_list'))

@app.route('/todos/<int:todo_id>/complete', methods=['POST'])
@login_required
def complete_todo(todo_id):
    todo = ToDoItem.query.get_or_404(todo_id)
    todo.completed = True
    db.session.commit()
    return redirect(url_for('get_todo_list'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', error='Username already exists')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('signup.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
