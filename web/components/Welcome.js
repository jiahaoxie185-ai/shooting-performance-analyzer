export default function Welcome({onLogin, onRegister}){
    return(
        <main>
            <h1>欢迎来到投篮训练</h1>
            <p>记录每一次投篮，查看训练成果</p>
            <button type="button" onClick={onLogin}>登陆</button>
            <button type="button" onClick={onRegister}>注册</button>
        </main>
    );
}