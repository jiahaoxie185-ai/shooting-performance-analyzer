# 测试投篮统计规则。
import unittest

from domain.shooting.rules import calculate_field_goals_percentage,calculate_zone_field_goals_percentage, calculate_shooting_summary, calculate_zone_statistics
from domain.shooting.entities import ShotAttempt, ShootingZone
from uuid import uuid4
from datetime import datetime

# 投篮统计规则测试；test_ 开头的方法会被 unittest 识别
class TestShootingRules(unittest.TestCase):
    # 验证空列表的命中率为零
    def test_no_shots_returns_zero(self):
        res = calculate_field_goals_percentage([])
        self.assertEqual(res, 0.0)

    # 验证三投两中的命中率为 2/3
    def test_two_made_one_missed(self):
        session_id = uuid4()
        attempt = []

        for made in [True, False, True]:
            shot = ShotAttempt(
                id=uuid4(),
                session_id= session_id,
                zone= ShootingZone,
                made= made,
                attempted_at= datetime.now()
            )
            attempt.append(shot)

        res = calculate_field_goals_percentage(attempt)

        self.assertAlmostEqual(res,2/3)

    # 验证篮下统计不包含其他区域的投篮
    def test_one_made_one_missed_in_paint(self):
        session_id = uuid4()
        attempt = []

        data = [
            (ShootingZone.PAINT, True),
            (ShootingZone.LEFT_CORNER, False),
            (ShootingZone.PAINT, False),
        ]

        for zone, made in data:
            shot = ShotAttempt(
                id=uuid4(),
                session_id=session_id,
                zone= zone,
                made = made,
                attempted_at= datetime.now()
            )
            attempt.append(shot)

        res = calculate_zone_field_goals_percentage(attempt, ShootingZone.PAINT)

        self.assertAlmostEqual(res, 1/2)

    # 验证总体统计的次数、命中数和命中率
    def test_shooting_summary(self):
        session_id = uuid4()
        attempts = []

        data = [
                    (ShootingZone.PAINT, True),
                    (ShootingZone.LEFT_CORNER, False),
                    (ShootingZone.PAINT, False),
                ]

        for zone,made in data:
            shot = ShotAttempt(
                id=uuid4(),
                session_id=session_id,
                zone=zone,
                made=made,
                attempted_at= datetime.now()
            )
            attempts.append(shot)


        res = calculate_shooting_summary(attempts) 

        self.assertEqual(res["attempts"], 3)   
        self.assertEqual(res["made"], 1)
        self.assertAlmostEqual(res["field_goals"], 1/3)

    # 验证区域汇总中篮下的统计结果
    def test_zone_statistics(self):
        session_id = uuid4()
        attempts = []

        data = [
                            (ShootingZone.PAINT, True),
                            (ShootingZone.LEFT_CORNER, False),
                            (ShootingZone.PAINT, False),
                        ]

        for zone, made in data:
            shot = ShotAttempt(
                id=uuid4(),
                session_id=session_id,
                zone=zone,
                made=made,
                attempted_at= datetime.now()
            )
            attempts.append(shot)

        res = calculate_zone_statistics(attempts)

        self.assertEqual(
            res["paint"],
            {
                "attempts": 2,
                "made": 1,
                "field_goals": 0.5
            }
        )
    
        
    

# 直接运行此模块时启动测试
if __name__ == "__main__":
    unittest.main()