from flask import Flask, request, jsonify, session, render_template  # Add render_template import
from routes.user_routes import user_bp, initialize_app
from models import db  # Add this import
from sympy import sympify, SympifyError  # 修正异常导入位置
from sympy.parsing.sympy_parser import parse_expr  # 移除 SympifyError 从此处导入
from sympy import Eq, solve, symbols, latex  # 其他原有导入
from models.user import User  # 添加User模型导入

app = Flask(__name__, instance_path='e:\\fc\\instance')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-here'

# Initialize database once
db.init_app(app)  # <-- This is the only initialization needed

with app.app_context():
    db.create_all()

# Remove this duplicate initialization
# db.init_app(app)  <-- Delete this line
app.config['SESSION_COOKIE_SECURE'] = False

# 只保留一次蓝图注册
app.register_blueprint(user_bp)
initialize_app(app)

# 修改上下文处理器（移除嵌套函数）
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.get_by_id(session['user_id'])
    return dict(current_user=user)  # 直接返回用户实例或None

@app.route('/')
def index():
    print(f"[DEBUG] 当前会话用户ID: {session.get('user_id')}")  # 添加调试日志
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve_equations():
    # 在try语句最前面添加使用记录
    if 'user_id' in session:
        user = User.get_by_id(session['user_id'])
        user.record_usage()
    data = request.json
    equations = data['equations']
    print(f"接收到的方程是：{equations}")
    try:
        all_symbols = set()
        for eq in equations:
            if len(eq) == 2:
                for side in eq:
                    parsed_side = side.replace(' ', '').replace(')(', ')*(').replace('][', ']*[')
                    expr = sympify(parsed_side)
                    all_symbols.update(expr.free_symbols)
        
        base_symbols = {s for s in all_symbols if not any(t in str(s) for t in ['*', '/', '**'])}
        variables = sorted([str(s) for s in base_symbols], key=lambda x: x.lower())

        # Build equation list
        eqlist = []
        for i, equation in enumerate(equations, 1):
            try:
                lhs, rhs = equation[0], equation[1]
                eqlist.append(Eq(sympify(lhs), sympify(rhs)))
            except (IndexError, TypeError, SympifyError) as e:  # 现在可以正确识别 SympifyError
                print(f"Equation {i} error: {e}")

        # Solve equations
        solutions = solve(eqlist, symbols(','.join(variables)), dict=True)

        # Serialize solutions
        serialized_solutions = {'solutions': [], 'variables': variables}
        if solutions:
            for sol in solutions:
                solution_dict = {}
                for var, val in sol.items():
                    solution_dict[str(var)] = {
                        'latex': latex(val.simplify()),
                        'str': str(val.simplify())
                    }
                if solution_dict:
                    serialized_solutions['solutions'].append(solution_dict)

        print(f"方程{data['equations']}的答案是：{serialized_solutions}")
        return jsonify(serialized_solutions)
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
