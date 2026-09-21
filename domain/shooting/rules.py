from .entities import ShotAttempt, ShootingZone

# 计算总命中率，返回 0～1 的比例
def calculate_field_goals_percentage(shots:list[ShotAttempt]) ->float:
    # 没有投篮时返回零，避免除以零
    if not shots:
        return 0.0

    made_count = 0
    for shot in shots:
        if shot.made is True:
            made_count += 1

    return made_count/len(shots)

# 筛选指定区域的投篮，再复用总命中率计算
def calculate_zone_field_goals_percentage(
        shots:list[ShotAttempt],
        zone:ShootingZone
) ->float:
    zone_shots = []

    for shot in shots:
        if shot.zone == zone:
            zone_shots.append(shot)

    return calculate_field_goals_percentage(zone_shots)

# 汇总投篮次数、命中次数和命中率
def calculate_shooting_summary(shots: list[ShotAttempt]) ->dict:
    made_count = 0

    for shot in shots:
        if shot.made:
            made_count += 1

    return {
        "attempts": len(shots),
        "made": made_count,
        "field_goals": calculate_field_goals_percentage(shots),
    }

# 返回所有区域的统计字典，没有投篮的区域也保留
def calculate_zone_statistics(shots: list[ShotAttempt])->dict:
    statistics = {}

    # 逐个区域筛选投篮，每轮重新创建该区域的列表
    for zone in ShootingZone:
        zone_shot = []

        for shot in shots:
            if shot.zone == zone:
                zone_shot.append(shot)

        # 用区域的字符串值作为键，保存计算后的统计结果
        statistics[zone.value] = calculate_shooting_summary(zone_shot)

    return statistics
