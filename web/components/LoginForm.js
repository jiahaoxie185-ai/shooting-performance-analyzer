export default function LoginForm({ onBack }){
    return(
        <main>
            <h1>登陆</h1>
            <section>            
                <label htmlFor="login-username">用户名</label>
                <input id="login-username" type="text" />

                <label htmlFor="login-password">密码</label>
                <input id="login-password" type="password" />

                <button type="button">登陆</button>
                <button type="button" onClick={onBack}>返回首页</button>
            </section>
        </main>
    );
}