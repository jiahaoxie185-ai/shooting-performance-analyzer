// 登录表单：填写用户名和密码；onBack 返回欢迎页。
export default function LoginForm({ onBack }){
    return(
        <main>
            <h1>登录</h1>
            <section>            
                <label htmlFor="login-username">用户名</label>
                <input id="login-username" type="text" />

                <label htmlFor="login-password">密码</label>
                <input id="login-password" type="password" />

                <button type="button">登录</button>
                <button type="button" onClick={onBack}>返回首页</button>
            </section>
        </main>
    );
}