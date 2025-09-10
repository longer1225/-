# game/card_factory.py

from .card import Card
from .skill import *

# ------------------ 牌号映射表 ------------------
# 每张牌的点数、孤立状态和技能列表
card_data_map = {
    1: {"points": 1, "is_isolated": False, "skills": [Skill_1()]},
    2: {"points": -1, "is_isolated": False, "skills": [Skill_2()]},
    3: {"points": 2, "is_isolated": False, "skills": [Skill_3()]},
    4: {"points": 0, "is_isolated": False, "skills": [Skill_4()]},
    5: {"points": 0, "is_isolated": False, "skills": [Skill_5()]},
    6: {"points": 0, "is_isolated": False, "skills": [Skill_6()]},
    7: {"points": 5, "is_isolated": False, "skills": [Skill_7()]},
    8: {"points": 4, "is_isolated": False, "skills": [Skill_8()]},
    9: {"points": 3, "is_isolated": False, "skills": [Skill_9()]},
    10: {"points": 2, "is_isolated": False, "skills": [Skill_10()]},
    # ---------------- 通用技能卡 ----------------
}

# ------------------ 工厂函数 ------------------
def create_card_by_number(number: int) -> Card:
    """
    根据牌号生成 Card 实例
    :param number: 牌号 (1~20)
    :return: Card 对象
    """
    data = card_data_map.get(number)
    if not data:
        raise ValueError(f"牌号 {number} 不存在映射表中！可用范围: {list(card_data_map.keys())}")
    return Card(
        name=str(number),
        points=data["points"],
        is_isolated=data["is_isolated"],
        skills=data["skills"]
    )

# ------------------ 测试 ------------------
if __name__ == "__main__":
    for i in range(1, 11):
        card = create_card_by_number(i)
        print(card.info())
