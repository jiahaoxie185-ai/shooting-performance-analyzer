export default function RegisterFrom({ onBack }) {
    return(
        <main>
            <h1>注册</h1>
            <section>
                <label htmlFor="register-username">用户名</label>
                < input id="register-username" type="text" />

                <label htmlFor="register-name">姓名</label>
                < input id="register-name" type="text" />

                <label htmlFor="register-password">密码</label>
                <input id="register-password" type="password" />
                <button type="button">注册</button>
                <button type="button" onClick={onBack}>返回首页</button>
            </section>
        </main>
    );
}