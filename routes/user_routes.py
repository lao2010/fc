from flask import Blueprint, render_template, redirect, session, request, jsonify
from models.user import User, init_db
from datetime import datetime

user_bp = Blueprint('user', __name__, url_prefix='/user')

def initialize_app(app):
    """Initialize the application with database setup"""
    # Remove the with app.app_context() and init_db() calls
    pass  # SQLAlchemy now handles initialization

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    if User.get_by_username(username):
        return jsonify({'error': '用户名已存在'}), 400
    
    user = User(username, email, password)
    user.save()
    return jsonify({'message': '注册成功'}), 201

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error variable
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get_by_username(username)
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect('/')
        error = '用户名或密码错误'  # Set error message
    return render_template('login.html', error=error)

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
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    user = User.get_by_id(session['user_id'])
    return jsonify({
        'remaining': user.check_usage(),
        'is_disabled': user.check_usage() <= 0
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