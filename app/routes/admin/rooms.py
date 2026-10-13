from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.admin_routes import admin_required
from app.database.admin_queries import get_all_rooms, create_room, update_room
from mysql.connector import Error

rooms_bp = Blueprint('admin_rooms', __name__, url_prefix='/admin/rooms')

@rooms_bp.route('/')
@admin_required
def index():
    rooms = get_all_rooms()
    return render_template('admin/rooms/index.html', rooms=rooms)

@rooms_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    form_data = {}
    if request.method == 'POST':
        form_data = request.form
        room_number = request.form.get('room_number', '').strip().upper()
        building = request.form.get('building', '').strip()
        floor_raw = request.form.get('floor', '1')
        capacity_raw = request.form.get('capacity', '30')

        if not room_number or not building:
            flash('Please specify both Room Number and Building name.', 'danger')
            return render_template('admin/rooms/form.html', room=None, form_data=form_data)

        try:
            floor = int(floor_raw)
            capacity = int(capacity_raw)
            create_room(room_number, building, floor, capacity)
            flash(f"Exam Room '{building} - {room_number}' created successfully.", 'success')
            return redirect(url_for('admin_rooms.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"Room '{room_number}' in building '{building}' already exists.", 'danger')
            else:
                flash('Unable to create room due to a database constraint error.', 'danger')
            return render_template('admin/rooms/form.html', room=None, form_data=form_data)
        except Exception:
            flash('An unexpected error occurred while creating the room.', 'danger')
            return render_template('admin/rooms/form.html', room=None, form_data=form_data)

    return render_template('admin/rooms/form.html', room=None, form_data=None)

@rooms_bp.route('/<int:room_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(room_id):
    rooms = get_all_rooms()
    room = next((r for r in rooms if r['room_id'] == room_id), None)
    if not room:
        flash('Exam Room not found.', 'danger')
        return redirect(url_for('admin_rooms.index'))

    if request.method == 'POST':
        room_number = request.form.get('room_number', '').strip().upper()
        building = request.form.get('building', '').strip()
        floor_raw = request.form.get('floor', '1')
        capacity_raw = request.form.get('capacity', '30')

        if not room_number or not building:
            flash('Please specify both Room Number and Building name.', 'danger')
            return render_template('admin/rooms/form.html', room=room, form_data=request.form)

        try:
            floor = int(floor_raw)
            capacity = int(capacity_raw)
            update_room(room_id, room_number, building, floor, capacity)
            flash(f"Exam Room '{building} - {room_number}' updated successfully.", 'success')
            return redirect(url_for('admin_rooms.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"Another room with number '{room_number}' already exists in '{building}'.", 'danger')
            else:
                flash('Unable to update room due to a database constraint error.', 'danger')
            return render_template('admin/rooms/form.html', room=room, form_data=request.form)
        except Exception:
            flash('An unexpected error occurred while updating the room.', 'danger')
            return render_template('admin/rooms/form.html', room=room, form_data=request.form)

    return render_template('admin/rooms/form.html', room=room, form_data=None)

@rooms_bp.route('/<int:room_id>/generate_seats', methods=['POST'])
@admin_required
def generate_seats(room_id):
    from app.database.operational_queries import generate_seats_for_room
    
    rows = int(request.form.get('rows', 5))
    cols = int(request.form.get('cols', 6))
    
    try:
        total = generate_seats_for_room(room_id, rows, cols)
        flash(f'Successfully generated {total} seats for the room.', 'success')
    except Exception as e:
        flash(f'Error generating seats: {e}', 'danger')
        
    return redirect(url_for('admin_rooms.index'))

