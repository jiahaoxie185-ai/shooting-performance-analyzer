// 欢迎页：提供进入登录和注册视图的按钮。
export default function Welcome({onLogin, onRegister}){
    return(
        <main>
            <h1>欢迎来到投篮训练</h1>
            <p>记录每一次投篮，查看训练成果</p>
            <button type="button" onClick={onLogin}>登录</button>
            <button type="button" onClick={onRegister}>注册</button>
        </main>
    );
}