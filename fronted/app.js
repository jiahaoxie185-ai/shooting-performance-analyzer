// 练习变量及控制台输出。
const username = "player01";
let attempts = 0;

attempts += 1;

console.log(username);
console.log(attempts);

// 根据布尔值返回投篮结果文字。
function shotResult(made){
    if (made){
        return "命中";
    }
    return "未命中";
}

console.log(shotResult(true))
console.log(shotResult(false))

// 用对象保存一条投篮记录。
const shot = {
    zone: "paint",
    made: true
};

console.log(shot.zone)
console.log(shot.made)


console.log(shotResult(shot.made))


// 用数组保存多条投篮记录。
const shots = [
    shot,
    { zone: "left_corner", made: false },
    { zone: "top_three", made: true },
];

console.log(shots.length);
console.log(shots[0].zone);

// 将每条记录转换为对应的区域名称。
const zones = shots.map((item) => item.zone);
console.log(zones)

// 筛选命中的投篮记录。
const madeShots = shots.filter((item) => item.made);
console.log(madeShots)
console.log(`field goals: ${madeShots.length} / ${shots.length}`);


// 用命中数和总次数计算百分比。
const fieldGoals = (madeShots.length / shots.length) * 100;
console.log(`field goals in persentage: ${fieldGoals.toFixed(1)}%`)

// 空数组先返回零，避免计算零除以零。
let noShots = [];

let noShotsRate = noShots.length === 0
? 0
: (noShots.filter((item) => item.made).length / noShots.length )* 100;

console.log(noShotsRate);//0

// 修改记录后，需要重新计算命中率。
noShots = [
    { zone: "left_corner", made: false },
    { zone: "top_three", made: true },
];


noShotsRate = noShots.length === 0
? 0
: (noShots.filter((item) => item.made).length / noShots.length )* 100;

console.log(noShotsRate);//50