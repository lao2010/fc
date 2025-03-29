import sys
sys.path.append('e:\\fc')
from flask import Flask, render_template, request, jsonify
from sympy import symbols, Eq, solve, sympify, latex  # 添加导入
from routes.user_routes import user_bp, initialize_app
from models import db  # Add this import

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Add database config
app.secret_key = 'development-key'

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()
app.config['SESSION_COOKIE_SECURE'] = False

# 只保留一次蓝图注册
app.register_blueprint(user_bp)
initialize_app(app)

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
            except (IndexError, TypeError, SympifyError) as e:
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
