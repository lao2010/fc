from flask import Flask, request, jsonify, session, render_template  # Add render_template import
from routes.user_routes import user_bp, initialize_app
from models import db  # Add this import
from sympy import sympify, SympifyError  # 修正异常导入位置
from sympy.parsing.sympy_parser import parse_expr  # 移除 SympifyError 从此处导入
from sympy import Eq, solve, symbols, latex  # 其他原有导入
from models.user import User  # 添加User模型导入

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Add this line
app.secret_key = 'development-key'

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()
app.config['SESSION_COOKIE_SECURE'] = False

# 只保留一次蓝图注册
app.register_blueprint(user_bp)
initialize_app(app)

# 在现有上下文处理器后添加调试输出
@app.context_processor
def inject_user():
    def get_current_user():
        if 'user_id' in session:
            user = User.get_by_id(session['user_id'])
            print(f"[DEBUG] Current User: {user.username if user else None}")  # 添加调试日志
            return user
        return None
    return dict(current_user=get_current_user)

@app.route('/')
def index():
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
