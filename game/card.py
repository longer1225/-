# game/card.py

class Card:
    def __init__(self, name, points, skills=None, is_isolated=False):
        """
        初始化卡牌
        :param name: 卡牌名称
        :param points: 卡牌基础点数
        :param skills: 技能对象列表（Skill 实例）
        :param is_isolated: 是否为孤立牌
        """
        self.name = name
        self.points = points
        self.skills = skills or []
        self.is_isolated = is_isolated

    def play(self, action):
        """
        出牌：
        1. 根据 is_isolated 放入玩家牌区
        2. 激活技能
        :param action: PlayAction 对象，包含 owner / self_card / board / targets
        """
        owner = action.owner

        # 放入牌区
        if self.is_isolated:
            owner.isolated_cards.append(self)
            print(f"{owner.name} 将 {self.name} 放入孤立区")
        else:
            owner.battlefield_cards.append(self)
            print(f"{owner.name} 将 {self.name} 放入战场")

        # 触发技能
        for skill in self.skills:
            skill.apply(action)

    def info(self):
        """返回卡牌信息（调试 / UI 用）"""
        return {
            "name": self.name,
            "points": self.points,
            "skills": [str(skill) for skill in self.skills],
            "is_isolated": self.is_isolated
        }

    def __str__(self):
        return f"Card({self.name}, points={self.points}, isolated={self.is_isolated})"
