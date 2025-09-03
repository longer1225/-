# game/card_factory.py

from card import Card
from skill import SkillAddPoint, SkillDestroyEnemy, SkillDrawCard

# ------------------ 牌号映射表 ------------------
# 每张牌的点数、孤立状态和技能列表
card_data_map = {
    1: {"points": 1, "is_isolated": False, "skills": [SkillAddPoint()]},
    2: {"points": -1, "is_isolated": True, "skills": [SkillDestroyEnemy()]},
    3: {"points": 2, "is_isolated": False, "skills": [SkillAddPoint(), SkillDestroyEnemy()]},
    4: {"points": 0, "is_isolated": False, "skills": [SkillDrawCard()]},
    # 继续写 5~20 号牌
}

# ------------------ 工厂函数 ------------------
def create_card_by_number(number):
    """
    根据牌号生成 Card 实例
    :param number: 牌号 (1~20)
    :return: Card 对象
    """
    data = card_data_map.get(number)
    if not data:
        raise ValueError(f"牌号 {number} 不存在映射表中！")
    return Card(
        name=str(number),
        points=data["points"],
        is_isolated=data["is_isolated"],
        skills=data["skills"]
    )

# ------------------ 测试 ------------------
if __name__ == "__main__":
    card1 = create_card_by_number(1)
    card2 = create_card_by_number(2)
    card3 = create_card_by_number(3)

    print(card1)
    print(card2.info())
    print(card3.info())
