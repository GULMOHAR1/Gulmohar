from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure secret key

# Configuration for file uploads
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('alumni_network.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    full_name = request.form['full_name']
    email = request.form['email']
    password = request.form['password']
    graduation_year = request.form['graduation_year']
    
    # Validate RVU email
    if not email.endswith('@rvu.edu.in'):
        flash('Please use your RVU email address (@rvu.edu.in)')
        return redirect(url_for('index'))
    
    # Determine user type based on graduation year
    current_year = datetime.now().year
    user_type = 'Alumni' if int(graduation_year) <= current_year else 'Student'
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (full_name, email, password_hash, graduation_year, user_type) VALUES (?, ?, ?, ?, ?)',
            (full_name, email, generate_password_hash(password), graduation_year, user_type)
        )
        conn.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        flash('Email already exists!')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['user_id']
        session['user_email'] = user['email']  # Store email for avatar generation
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email or password')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all posts with user information
    posts = cursor.execute('''
        SELECT posts.*, users.full_name, users.email
        FROM posts
        JOIN users ON posts.user_id = users.user_id
        ORDER BY posts.created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         user_email=session.get('user_email', ''),
                         posts=posts)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    content = request.form.get('content')
    link_url = request.form.get('link_url')
    image_url = None

    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            # Generate a secure filename with timestamp to avoid duplicates
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = f'/static/uploads/{filename}'
            print(f"Image saved to: {filepath}")  # Debug print

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (user_id, content, image_url, link_url, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], content, image_url, link_url, datetime.now()))
        conn.commit()
    except Exception as e:
        print(f"Error creating post: {e}")  # Debug print
        flash('Error creating post')
    finally:
        conn.close()

    return redirect(url_for('dashboard'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user information
    user = cursor.execute('SELECT * FROM users WHERE user_id = ?', 
                         (session['user_id'],)).fetchone()
    
    # Get user's posts with datetime conversion
    user_posts = cursor.execute('''
        SELECT post_id, 
               user_id, 
               content, 
               image_url, 
               link_url, 
               datetime(created_at) as created_at 
        FROM posts 
        WHERE user_id = ? 
        ORDER BY created_at DESC''', 
        (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('profile.html', user=user, user_posts=user_posts)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get form data
    graduation_year = request.form.get('graduation_year')
    department = request.form.get('department')  # New field
    location = request.form.get('location')
    current_status = request.form.get('current_status')
    job_role = request.form.get('job_role')
    website = request.form.get('website')
    bio = request.form.get('bio')
    linkedin = request.form.get('linkedin')
    github = request.form.get('github')
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET graduation_year = ?,
                department = ?,
                location = ?,
                current_status = ?,
                job_role = ?,
                website = ?,
                bio = ?,
                linkedin = ?,
                github = ?,
                is_profile_completed = TRUE
            WHERE user_id = ?
        ''', (graduation_year, department, location, current_status, 
              job_role, website, bio, linkedin, github, session['user_id']))
        conn.commit()
        flash('Profile updated successfully!')
    except Exception as e:
        flash('Error updating profile')
        print(f"Error: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('profile'))

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if 'profile_picture' not in request.files:
        flash('No file selected')
        return redirect(url_for('profile'))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"profile_{session['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Update database with new profile picture URL
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET profile_picture = ? 
                WHERE user_id = ?
            ''', (f'/static/uploads/{filename}', session['user_id']))
            conn.commit()
            flash('Profile picture updated successfully!')
        except Exception as e:
            flash('Error updating profile picture')
            print(f"Error: {e}")
        finally:
            conn.close()
    else:
        flash('Invalid file type')
    
    return redirect(url_for('profile'))

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Verify post belongs to user
        post = cursor.execute('SELECT * FROM posts WHERE post_id = ? AND user_id = ?', 
                            (post_id, session['user_id'])).fetchone()
        
        if post:
            # Delete the post's image if it exists
            if post['image_url']:
                try:
                    image_path = os.path.join('static', post['image_url'].split('/static/')[1])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    print(f"Error deleting image: {e}")
            
            # Delete the post
            cursor.execute('DELETE FROM posts WHERE post_id = ?', (post_id,))
            conn.commit()
            flash('Post deleted successfully!')
        else:
            flash('Post not found or unauthorized')
    except Exception as e:
        flash('Error deleting post')
        print(f"Error: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('profile'))

@app.route('/delete_account')
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Delete user's posts and their associated images
        posts = cursor.execute('SELECT * FROM posts WHERE user_id = ?', 
                             (session['user_id'],)).fetchall()
        for post in posts:
            if post['image_url']:
                try:
                    image_path = os.path.join('static', post['image_url'].split('/static/')[1])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    print(f"Error deleting post image: {e}")
        
        # Delete user's profile picture if it exists
        user = cursor.execute('SELECT profile_picture FROM users WHERE user_id = ?', 
                            (session['user_id'],)).fetchone()
        if user and user['profile_picture']:
            try:
                image_path = os.path.join('static', user['profile_picture'].split('/static/')[1])
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting profile picture: {e}")
        
        # Delete user's data
        cursor.execute('DELETE FROM posts WHERE user_id = ?', (session['user_id'],))
        cursor.execute('DELETE FROM users WHERE user_id = ?', (session['user_id'],))
        conn.commit()
        
        session.clear()
        flash('Account deleted successfully')
    except Exception as e:
        flash('Error deleting account')
        print(f"Error: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/connections')
def connections():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all users except current user
    users = cursor.execute('''
        SELECT user_id, full_name, email, graduation_year as batch, department 
        FROM users 
        WHERE user_id != ?
        ORDER BY full_name
    ''', (session['user_id'],)).fetchall()
    
    # Get pending connection requests (notifications)
    notifications = cursor.execute('''
        SELECT 
            c.connection_id,
            u.full_name as sender_name,
            u.email as sender_email
        FROM connections c
        JOIN users u ON c.sender_id = u.user_id
        WHERE c.receiver_id = ? AND c.status = 'pending'
    ''', (session['user_id'],)).fetchall()
    
    # Get existing connections
    existing_connections = cursor.execute('''
        SELECT 
            CASE 
                WHEN sender_id = ? THEN receiver_id 
                WHEN receiver_id = ? THEN sender_id 
            END as connected_user_id,
            status
        FROM connections 
        WHERE (sender_id = ? OR receiver_id = ?)
    ''', (session['user_id'], session['user_id'], 
          session['user_id'], session['user_id'])).fetchall()
    
    conn.close()
    
    # Create a dict of connected user IDs and their status
    connected_users = {conn['connected_user_id']: conn['status'] 
                      for conn in existing_connections if conn['connected_user_id']}
    
    return render_template('connections.html', 
                         users=users,
                         notifications=notifications,
                         connected_users=connected_users)

@app.route('/send_connection_request', methods=['POST'])
def send_connection_request():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    receiver_id = request.form.get('receiver_id')
    if not receiver_id:
        flash('Invalid request')
        return redirect(url_for('connections'))
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if connection already exists
        existing = cursor.execute('''
            SELECT * FROM connections 
            WHERE (sender_id = ? AND receiver_id = ?) 
               OR (sender_id = ? AND receiver_id = ?)
        ''', (session['user_id'], receiver_id, 
              receiver_id, session['user_id'])).fetchone()
        
        if not existing:
            cursor.execute('''
                INSERT INTO connections (sender_id, receiver_id, status)
                VALUES (?, ?, 'pending')
            ''', (session['user_id'], receiver_id))
            conn.commit()
            flash('Connection request sent!')
        else:
            flash('Connection already exists')
    except Exception as e:
        print(f"Error: {e}")
        flash('Error sending connection request')
    finally:
        conn.close()
    
    return redirect(url_for('connections'))

@app.route('/handle_connection_request', methods=['POST'])
def handle_connection_request():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    connection_id = request.form.get('connection_id')
    action = request.form.get('action')  # 'accept' or 'decline'
    
    if not connection_id or action not in ['accept', 'decline']:
        flash('Invalid request')
        return redirect(url_for('connections'))
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if action == 'accept':
            cursor.execute('''
                UPDATE connections 
                SET status = 'accepted' 
                WHERE connection_id = ? AND receiver_id = ?
            ''', (connection_id, session['user_id']))
        else:
            cursor.execute('''
                DELETE FROM connections 
                WHERE connection_id = ? AND receiver_id = ?
            ''', (connection_id, session['user_id']))
        conn.commit()
        flash(f'Connection request {action}ed!')
    except Exception as e:
        print(f"Error: {e}")
        flash('Error handling connection request')
    finally:
        conn.close()
    
    return redirect(url_for('connections'))

@app.route('/events')
def events():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all events with organizer information
    events = cursor.execute('''
        SELECT 
            e.*,
            u.full_name as organizer_name,
            COUNT(ep.user_id) as participant_count,
            CASE WHEN ep2.user_id IS NOT NULL THEN 1 ELSE 0 END as is_participating
        FROM events e
        JOIN users u ON e.organizer_id = u.user_id
        LEFT JOIN event_participants ep ON e.event_id = ep.event_id
        LEFT JOIN event_participants ep2 ON e.event_id = ep2.event_id AND ep2.user_id = ?
        WHERE e.date >= DATE('now')
        GROUP BY e.event_id
        ORDER BY e.date ASC, e.time ASC
    ''', (session['user_id'],)).fetchall()
    
    # Get notifications (reuse your existing notification query)
    notifications = cursor.execute('''
        SELECT 
            c.connection_id,
            u.full_name as sender_name,
            u.email as sender_email
        FROM connections c
        JOIN users u ON c.sender_id = u.user_id
        WHERE c.receiver_id = ? AND c.status = 'pending'
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('events.html', events=events, notifications=notifications)

@app.route('/create_event', methods=['POST'])
def create_event():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    title = request.form.get('title')
    date = request.form.get('date')
    time = request.form.get('time')
    description = request.form.get('description')
    location = request.form.get('location')
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO events (title, description, date, time, location, organizer_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, date, time, location, session['user_id']))
        conn.commit()
        flash('Event created successfully!')
    except Exception as e:
        print(f"Error creating event: {e}")
        flash('Error creating event')
    finally:
        conn.close()
    
    return redirect(url_for('events'))

@app.route('/rsvp_event', methods=['POST'])
def rsvp_event():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    event_id = request.form.get('event_id')
    action = request.form.get('action')  # 'going' or 'cancel'
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if action == 'going':
            cursor.execute('''
                INSERT OR REPLACE INTO event_participants (event_id, user_id, status)
                VALUES (?, ?, 'going')
            ''', (event_id, session['user_id']))
        else:
            cursor.execute('''
                DELETE FROM event_participants
                WHERE event_id = ? AND user_id = ?
            ''', (event_id, session['user_id']))
        conn.commit()
        flash('RSVP updated successfully!')
    except Exception as e:
        print(f"Error updating RSVP: {e}")
        flash('Error updating RSVP')
    finally:
        conn.close()
    
    return redirect(url_for('events'))

if __name__ == '__main__':
    app.run(debug=True) 