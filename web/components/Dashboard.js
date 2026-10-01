// 训练工作台：登录后显示的各个功能区块，目前只有标题。
export default function Dashboard(){
  return(
    <div>
      <section>
        <h3>创建单次投篮场次</h3>
      </section>

      <section>
        <h3>添加投篮</h3>
      </section>

      <section>
        <h3>单次投篮场次总结</h3>
      </section>

      <section>
        <h3>全部投篮训练场次</h3>
      </section>

      <section>
        <h3>总命中率</h3>
      </section>
    </div>
  );
}