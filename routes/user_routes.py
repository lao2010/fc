from flask import Blueprint, render_template, redirect, session, request, jsonify
from models.user import User, init_db
from datetime import datetime
from flask import flash
from flask import Flask, redirect, url_for, session, request, flash  # 添加url_for导入

user_bp = Blueprint('user', __name__, url_prefix='/user')

def initialize_app(app):
    """Initialize the application with database setup"""
    # Remove the with app.app_context() and init_db() calls
    pass  # SQLAlchemy now handles initialization

@user_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    email = request.form.get('email', '').strip()

    # Add validation for required fields
    if not username or not password:
        flash('用户名和密码不能为空')
        return redirect('/user/register')
    
    # Create user without password in constructor
    new_user = User(username=username, email=email)
    new_user.set_password(password)  # Set password via method
    
    db.session.add(new_user)
    db.session.commit()
    
    return redirect('/user/login')

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Add debug logging
        print(f"[AUTH] Login attempt - Username: {username}")
        
        user = User.get_by_username(username)
        if user:
            print(f"[AUTH] User found - Password match: {user.check_password(password)}")
            
        if not user or not user.check_password(password):
            flash('用户名或密码错误')
            return redirect(url_for('user.login'))  # 现在可以正确调用url_for
            
        session['user_id'] = user.id
        session.modified = True
        print(f"[AUTH] Login successful - User ID: {user.id}")
        return redirect(url_for('index'))  # Redirect to main page
    
    # Handle GET requests
    return render_template('login.html')

@user_bp.route('/register', methods=['GET'])
def show_register():
    return render_template('register.html')

@user_bp.route('/register', methods=['POST'])
def handle_register():
    if not request.is_json:
        return jsonify({'error': '请求必须使用JSON格式'}), 415
        
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码必填'}), 400
        
    if User.get_by_username(username):
        return jsonify({'error': '用户已存在'}), 409
    
    try:
        User.create_user(username, password)
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 添加使用记录路由
@user_bp.route('/history')
def history():
    if 'user_id' not in session:
        return redirect('/login')
    user = User.get_by_id(session['user_id'])
    return render_template('history.html', history=user.get_usage_history())

# 保护解方程路由
@user_bp.before_request
def check_auth():
    if request.endpoint == 'solve_equations':
        if 'user_id' not in session:
            return jsonify({'error': '请先登录'}), 401
            
        user = User.get_by_id(session['user_id'])
        if user.check_usage() <= 0:
            return jsonify({'error': '今日使用次数已用完'}), 403

@user_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/user/login')
        
    user = User.get_by_id(session['user_id'])
    return render_template('profile.html', user=user)  # 添加用户对象传递

@user_bp.route('/check_status')
def check_status():
    # 后续可添加真实用户状态检查
    return jsonify({'logged_in': True})

@user_bp.route('/check_usage')
def check_usage():
    user = None
    if 'user_id' in session:
        user = User.get_by_id(session['user_id'])
    
    # Return basic state even when not logged in
    return jsonify({
        'logged_in': user is not None,
        'remaining': user.check_usage() if user else 0,
        'is_disabled': user.check_usage() <= 0 if user else True
    })

@user_bp.route('/update_password', methods=['POST'])
def update_password():
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    user = User.get_by_id(session['user_id'])
    if not user.check_password(old_password):
        return jsonify({'error': '原密码错误'}), 400
    
    user.update_password(new_password)
    return jsonify({'message': '密码修改成功'})

@user_bp.route('/update_email', methods=['POST'])
def update_email():
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    data = request.json
    new_email = data.get('new_email')
    
    user = User.get_by_id(session['user_id'])
    user.update_email(new_email)
    return jsonify({'message': '邮箱修改成功'})

@user_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@user_bp.route('/test_session')
def test_session():
    if 'user_id' in session:
        return jsonify({'status': 'logged in', 'user_id': session['user_id']})
    return jsonify({'status': 'not logged in'})

@user_bp.route('/debug_session')
def debug_session():
    return jsonify({
        'session_data': dict(session),
        'is_logged_in': 'user_id' in session
    })

@user_bp.route('/check_session')
def check_session():
    if 'user_id' not in session:
        return jsonify({'logged_in': False})
    
    user = User.get_by_id(session['user_id'])
    return jsonify({
        'logged_in': True,
        'remain': user.check_usage() if user else 0
    })

# 确保使用正确的蓝图对象定义路由
@user_bp.route('/')  # 修改前是 @app.route('/')
def home():
    return "User Home Page"