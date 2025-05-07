from flask import Flask, request, jsonify, render_template, redirect, url_for
from datetime import datetime
from supabase import create_client, Client

app = Flask(__name__)

# Configuración de Supabase con tus credenciales
supabase_url = "https://cpwyoghklhxmnrgwzpbe.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNwd3lvZ2hrbGh4bW5yZ3d6cGJlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY1ODM5NjUsImV4cCI6MjA2MjE1OTk2NX0.IReQDSqPAKU12IVwUSPjGEgE5pf4auWJ3fNsTV9jJKM"
supabase: Client = create_client(supabase_url, supabase_key)

# Función para obtener la fecha actual
def get_current_date():
    return datetime.now().strftime('%Y-%m-%d')

# Agregar la función now() al contexto de Jinja2
@app.context_processor
def utility_processor():
    def now():
        return datetime.now()
    return dict(now=now)

# Ruta principal - Lista todas las tareas
@app.route('/')
def index():
    filter_status = request.args.get('filter', 'all')
    
    query = supabase.table('tasks').select('*')
    
    if filter_status == 'completed':
        query = query.eq('completed', True)
    elif filter_status == 'pending':
        query = query.eq('completed', False)
    
    # Ordenar por fecha de vencimiento (primero las que vencen pronto)
    # y luego por fecha de creación (las más recientes primero)
    response = query.order('due_date', desc=False).order('created_at', desc=True).execute()
    
    tasks = response.data
    return render_template('index.html', tasks=tasks, filter=filter_status, current_date=get_current_date())

# Crear una nueva tarea
@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.form
    task_data = {
        'title': data.get('title'),
        'description': data.get('description'),
        'completed': False
    }
    
    # Agregar fecha de vencimiento si se proporciona
    due_date = data.get('due_date')
    if due_date and due_date.strip():
        task_data['due_date'] = due_date
    
    response = supabase.table('tasks').insert(task_data).execute()
    return redirect(url_for('index'))

# Obtener una tarea específica
@app.route('/tasks/<int:task_id>')
def get_task(task_id):
    response = supabase.table('tasks').select('*').eq('id', task_id).execute()
    task = response.data[0] if response.data else None
    
    if task:
        return render_template('task_detail.html', task=task, current_date=get_current_date())
    return jsonify({"error": "Tarea no encontrada"}), 404

# Actualizar una tarea
@app.route('/tasks/<int:task_id>', methods=['POST'])
def update_task(task_id):
    data = request.form
    task_data = {
        'title': data.get('title'),
        'description': data.get('description')
    }
    
    # Agregar fecha de vencimiento si se proporciona
    due_date = data.get('due_date')
    if due_date and due_date.strip():
        task_data['due_date'] = due_date
    else:
        task_data['due_date'] = None
    
    response = supabase.table('tasks').update(task_data).eq('id', task_id).execute()
    return redirect(url_for('get_task', task_id=task_id))

# Marcar tarea como completada/pendiente
@app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    # Primero obtenemos el estado actual
    response = supabase.table('tasks').select('completed').eq('id', task_id).execute()
    task = response.data[0] if response.data else None
    
    if task:
        # Invertimos el estado
        new_status = not task['completed']
        response = supabase.table('tasks').update({'completed': new_status}).eq('id', task_id).execute()
    
    # Redirigir de vuelta a la página anterior
    return redirect(request.referrer or url_for('index'))

# Eliminar una tarea
@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    response = supabase.table('tasks').delete().eq('id', task_id).execute()
    return redirect(url_for('index'))

# Formulario para editar tarea
@app.route('/tasks/<int:task_id>/edit')
def edit_task(task_id):
    response = supabase.table('tasks').select('*').eq('id', task_id).execute()
    task = response.data[0] if response.data else None
    
    if task:
        return render_template('edit_task.html', task=task)
    return jsonify({"error": "Tarea no encontrada"}), 404

# Formulario para crear tarea
@app.route('/tasks/new')
def new_task():
    return render_template('new_task.html')

if __name__ == '__main__':
    app.run(debug=True)