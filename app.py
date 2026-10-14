from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(30), default='Planning')
    priority = db.Column(db.String(20), default='Medium')
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    assignee = db.Column(db.String(100), default='Unassigned')
    status = db.Column(db.String(30), default='To Do')
    priority = db.Column(db.String(20), default='Medium')
    due_date = db.Column(db.Date, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))

def parse_date(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date() if value else None
    except ValueError:
        return None

@app.route('/')
def dashboard():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    tasks = Task.query.order_by(Task.id.desc()).all()
    counts = {'projects': len(projects), 'active': sum(p.status == 'In Progress' for p in projects),
              'tasks': len(tasks), 'completed': sum(t.status == 'Done' for t in tasks)}
    return render_template('dashboard.html', projects=projects, tasks=tasks, counts=counts, today=date.today())

@app.route('/projects/add', methods=['POST'])
def add_project():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Project name is required.', 'error')
        return redirect(url_for('dashboard'))
    project = Project(name=name, description=request.form.get('description', '').strip(),
                      status=request.form.get('status', 'Planning'), priority=request.form.get('priority', 'Medium'),
                      due_date=parse_date(request.form.get('due_date', '')))
    db.session.add(project)
    db.session.commit()
    flash('Project created successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/projects/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    Task.query.filter_by(project_id=project.id).delete()
    db.session.delete(project)
    db.session.commit()
    flash('Project and its tasks deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/tasks/add', methods=['POST'])
def add_task():
    title = request.form.get('title', '').strip()
    if not title:
        flash('Task title is required.', 'error')
        return redirect(url_for('dashboard'))
    project_id = request.form.get('project_id')
    task = Task(title=title, assignee=request.form.get('assignee', '').strip() or 'Unassigned',
                status=request.form.get('status', 'To Do'), priority=request.form.get('priority', 'Medium'),
                due_date=parse_date(request.form.get('due_date', '')),
                project_id=int(project_id) if project_id else None)
    db.session.add(task)
    db.session.commit()
    flash('Task added successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/tasks/<int:task_id>/status', methods=['POST'])
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    status = request.form.get('status', 'To Do')
    task.status = status if status in ['To Do', 'In Progress', 'Done'] else 'To Do'
    db.session.commit()
    flash('Task status updated.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'success')
    return redirect(url_for('dashboard'))

with app.app_context():
    db.create_all()
    if Project.query.count() == 0:
        p1 = Project(name='Website Redesign', description='Refresh the company website and improve mobile usability.', status='In Progress', priority='High', due_date=date(2026, 11, 5))
        p2 = Project(name='Mobile App MVP', description='Build the first version of the customer mobile app.', status='Planning', priority='Medium', due_date=date(2026, 12, 10))
        p3 = Project(name='Marketing Campaign', description='Prepare launch content and campaign reporting.', status='Completed', priority='Low', due_date=date(2026, 10, 20))
        db.session.add_all([p1, p2, p3]); db.session.flush()
        db.session.add_all([
            Task(title='Create dashboard wireframes', assignee='Ananya', status='Done', priority='High', due_date=date(2026, 10, 12), project_id=p1.id),
            Task(title='Build responsive navigation', assignee='Bhargavi', status='In Progress', priority='High', due_date=date(2026, 10, 18), project_id=p1.id),
            Task(title='Review API requirements', assignee='Rahul', status='To Do', priority='Medium', due_date=date(2026, 10, 22), project_id=p2.id),
            Task(title='Prepare launch checklist', assignee='Meera', status='Done', priority='Low', due_date=date(2026, 10, 10), project_id=p3.id)])
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
