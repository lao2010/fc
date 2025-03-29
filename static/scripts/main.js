// 实时更新按钮状态
function updateSolveButton() {
    fetch('/user/check_session')
        .then(res => res.json())
        .then(data => {
            const btn = document.getElementById('solve-btn');
            if(data.logged_in) {
                btn.textContent = `开始解方程 (剩余${data.remain}次)`;
                btn.disabled = data.remain <= 0;
            }
        });
}

// 每60秒检查一次使用次数
function updateButtonState() {
    fetch('/user/check_usage', {
        credentials: 'same-origin'  // 添加cookie传递
    })
    .then(res => {
        if(res.status === 401) {
            // 强制刷新页面以更新导航栏状态
            window.location.reload();
            return;
        }
        return res.json();
    })
    .then(data => {
        const solveBtn = document.getElementById('solve-btn');
        if (!solveBtn) {
            console.log('Solve button not found');
            return;
        }

        console.log('Updating button state...');
        fetch('/user/check_usage')
            .then(res => {
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                return res.json();
            })
            .then(data => {
                console.log('API response:', data);
                solveBtn.textContent = `开始解方程 (剩余${data.remaining}次)`;
                solveBtn.disabled = data.is_disabled;
                solveBtn.className = `solve-btn ${data.is_disabled ? 'disabled' : ''}`;
            })
            .catch(error => {
                console.error('Error fetching usage:', error);
                solveBtn.textContent = '开始解方程';
                solveBtn.disabled = true;
            });
    });
}

// 添加点击事件监听测试
document.getElementById('solve-btn')?.addEventListener('click', function(e) {
    if(this.disabled) {
        alert('今日使用次数已耗尽！');
        e.preventDefault();
    }
});

// 每30秒更新一次状态 + 页面加载时更新
document.addEventListener('DOMContentLoaded', updateButtonState);
setInterval(updateButtonState, 30000);

// 每5分钟更新一次
setInterval(updateSolveButton, 300000);

// 在原有代码后添加
function initNavState() {
    const navButtons = document.querySelector('.nav-buttons');
    if(!navButtons) return;
    
    // 强制刷新按钮状态
    fetch('/user/check_usage').then(res => res.json()).then(data => {
        const solveBtn = document.getElementById('solve-btn');
        if(solveBtn) {
            solveBtn.textContent = `${data.remaining}次可用`;
            solveBtn.disabled = data.is_disabled;
        }
    });
}

// 页面加载和路由切换时都执行
document.addEventListener('DOMContentLoaded', initNavState);
window.addEventListener('popstate', initNavState);