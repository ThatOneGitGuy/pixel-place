from flask import Flask, request, jsonify, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_user, create_user, get_pixel, claim_pixel, update_pixel_color, get_all_pixels, get_free_pixels, is_valid_pixel_id
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400

    pw_hash = generate_password_hash(password)
    if create_user(username, pw_hash):
        session['username'] = username
        return jsonify({'success': True, 'username': username})
    else:
        return jsonify({'error': 'Username already taken'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    user = get_user(username)
    if user and check_password_hash(user['password_hash'], password):
        session['username'] = username
        return jsonify({'success': True, 'username': username, 'pixel_id': user['pixel_id']})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/api/me')
def me():
    username = session.get('username')
    if not username:
        return jsonify({'logged_in': False})
    user = get_user(username)
    return jsonify({'logged_in': True, 'username': username, 'pixel_id': user['pixel_id']})

@app.route('/api/pixels')
def pixels():
    return jsonify(get_all_pixels())

@app.route('/api/pixel/<pixel_id>')
def pixel_info(pixel_id):
    pixel = get_pixel(pixel_id)
    if pixel:
        return jsonify(pixel)
    return jsonify({'pixel_id': pixel_id, 'owner': None, 'color': '#FFFFFF'})

@app.route('/api/claim', methods=['POST'])
def claim():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401

    user = get_user(username)
    if user['pixel_id']:
        return jsonify({'error': 'You already own a pixel'}), 400

    data = request.json
    pixel_id = data.get('pixel_id', '').strip()
    color = data.get('color', '#8b5e3c')
    random_pick = data.get('random', False)

    if random_pick:
        free = get_free_pixels(1)
        if not free:
            return jsonify({'error': 'No pixels available'}), 400
        pixel_id = free[0]
    else:
        if not pixel_id:
            return jsonify({'error': 'No pixel ID provided'}), 400
        if not is_valid_pixel_id(pixel_id):
            return jsonify({'error': 'Invalid pixel ID. Use format row-col, e.g. 1-1 or 150-200'}), 400
        existing = get_pixel(pixel_id)
        if existing and existing['owner']:
            return jsonify({'error': f'Pixel {pixel_id} is already taken'}), 400

    if claim_pixel(pixel_id, username, color):
        return jsonify({'success': True, 'pixel_id': pixel_id, 'color': color})
    else:
        return jsonify({'error': 'Could not claim pixel (already taken)'}), 400

@app.route('/api/update_color', methods=['POST'])
def update_color():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'Not logged in'}), 401

    user = get_user(username)
    if not user['pixel_id']:
        return jsonify({'error': 'You do not own a pixel yet'}), 400

    data = request.json
    color = data.get('color', '#8b5e3c')
    update_pixel_color(user['pixel_id'], username, color)
    return jsonify({'success': True, 'pixel_id': user['pixel_id'], 'color': color})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)