// 保留原有拦截器逻辑
axios.interceptors.response.use(response => {
    if (response.data.code !== 200) {
        return Promise.reject(response.data);
    }
    return response.data;
}, error => {
    return Promise.reject({ 
        code: error.response?.status || 500,
        message: error.response?.data?.message || '网络异常'
    });
});

// 增强服务对象
const userService = {
    login: async (params) => {
        try {
            return await axios.post('/api/user/login', params);
        } catch (error) {
            return { code: 500, message: '服务器连接异常' };
        }
    },
    // 新增注册方法
    register: async (data) => {
        try {
            return await axios.post('/api/user/register', data);
        } catch (error) {
            return { code: error.code || 500, message: error.message };
        }
    }
};

// 导出逻辑保持兼容
if (typeof module !== 'undefined' && module.exports) {
    module.exports = userService; // 保留原有模块系统
} else {
    window.userService = userService; // 新增浏览器环境支持
}