document.addEventListener('DOMContentLoaded', function() {
    const equationsForm = document.getElementById('equations-form');
    const addEquationButton = document.getElementById('add-equation');
    const solveButton = document.getElementById('solve');
    const resultContainer = document.getElementById('result');

    // 确保addEquationButton事件监听器只添加一个
    addEquationButton.addEventListener('click', function() {
        const newEquationInput = document.createElement('input');
        newEquationInput.type = 'text';
        newEquationInput.name = 'equation';
        newEquationInput.placeholder = 'Enter equation';

        const removeButton = document.createElement('button');
        removeButton.textContent = 'Remove';
        removeButton.addEventListener('click', function() {
            equationsForm.removeChild(newEquationInput);
            equationsForm.removeChild(removeButton);
        });

        equationsForm.appendChild(newEquationInput);
        equationsForm.appendChild(removeButton);
    });

    solveButton.addEventListener('click', function() {
        const equationInputs = document.querySelectorAll('#equations-form input[name="equation"]');
        
        // 修改后的方程收集逻辑（增加容错处理）
        const equations = [];
        let hasValidEquation = false;
        
        equationInputs.forEach(input => {
            input.style.border = ""; // 重置边框样式
            try {
                // 处理全角等号并规范化输入
                let equationStr = input.value.trim()
                    .replace(/＝/g, '=')  // 替换全角等号
                    .replace(/\^/g, '**') // 转换幂运算符
                    // 添加乘法符号自动插入
                    .replace(/(\d)([a-zA-Z])/g, '$1*$2')  // 数字后接字母 → 插入*
                    .replace(/([a-zA-Z])(\d)/g, '$1*$2')  // 字母后接数字 → 插入*
                    .replace(/([)\]}])([a-zA-Z])/g, '$1*$2') // 括号后接字母 → 插入*
                    .replace(/([a-zA-Z])([(\[{])/g, '$1*$2'); // 字母后接括号 → 插入*

                if (!equationStr) return;  // 跳过空输入

                if (!equationStr.includes("=")) {
                    throw new Error(`方程必须包含等号，当前输入: ${equationStr}`);
                }

                const parts = equationStr.split('=');
                if (parts.length !== 2) {
                    throw new Error(`只能有一个等号，当前输入: ${equationStr}`);
                }

                const [leftSide, rightSide] = parts.map(s => s.trim());
                if (!leftSide || !rightSide) {
                    throw new Error(`方程不完整: ${equationStr}`);
                }

                equations.push([leftSide, rightSide]);
                hasValidEquation = true;

            } catch (error) {
                input.style.border = "2px solid red";
                console.warn('方程解析失败:', error.message);
            }
        });

        if (!hasValidEquation) {
            resultContainer.textContent = "错误：至少需要输入一个有效方程";
            return;
        }

        // 修改后的请求体
        fetch('/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equations: equations })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                resultContainer.textContent = '错误: ' + data.error;
            } else if (data.solutions?.length > 0) {
                // 添加加载状态提示
                resultContainer.innerHTML = '<div class="loading">公式渲染中...</div>';
                
                // 延迟执行确保DOM更新
                setTimeout(() => {
                    resultContainer.innerHTML = data.solutions.map((solSet, idx) => `
                        <div class="solution-group">
                            <h3>解集 ${idx + 1}</h3>
                            ${Object.entries(solSet).map(([varName, expr]) => `
                                <div class="math-render">
                                    \\(${varName} = ${expr.latex.replace(/\*\*/g, '^')}\\)
                                </div>
                            `).join('')}
                        </div>
                    `).join('');
                    MathJax.typesetPromise();
                }, 50);
            } else {
                resultContainer.textContent = '未找到有效解';
            }
        })
        .catch(error => {
            console.error('请求失败:', error);
            resultContainer.textContent = '方程求解失败，请检查输入格式';
        });
    });
});
