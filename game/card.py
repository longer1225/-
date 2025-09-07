# game/card.py

class Card:
    def __init__(self, name, points, skills=None, is_isolated=False):
        """
        初始化卡牌

        :param name: 卡牌名称（字符串或牌号）
        :param points: 卡牌自带点数（整数，可正可负）
        :param skills: 技能对象列表（Skill 实例）
        :param is_isolated: 是否为孤立牌（布尔值）
        """
        self.name = name
        self.points = points
        self.skills = skills or []  # 支持多技能
        self.is_isolated = is_isolated

    def activate_skills(self, owner, board=None):
        """
        遍历技能列表依次触发
        技能内部决定是否需要玩家选择目标
        :param owner: 出牌的玩家对象
        :param board: 游戏 Board 对象（访问所有玩家）
        """
        for skill in self.skills:
            if getattr(skill, "needs_target", False):
                # 需要玩家选择目标的技能，调用 UI 获取目标
                target_card = ui_get_target_card(board)  # UI 弹窗或点击事件
                skill.apply(owner=owner, board=board, self_card=self, target_card=target_card)
            elif getattr(skill, "needs_targets", False):
                # 多目标技能，UI 选择多个目标
                targets = ui_get_targets(board)  # 返回列表
                skill.apply(owner=owner, board=board, self_card=self, targets=targets)
            else:
                # 无需目标的技能
                skill.apply(owner=owner, board=board, self_card=self)

    def play(self, owner, board=None):
        """
        玩家出牌操作
        1. 根据 is_isolated 放入玩家自己的牌区
        2. 激活技能效果
        :param owner: 出牌的玩家对象
        :param board: 游戏的 Board 对象
        """
        # 放入玩家自己的牌区
        if self.is_isolated:
            owner.isolated_cards.append(self)
            print(f"{owner.name} 将 {self.name} 放入孤立区")
        else:
            owner.battlefield_cards.append(self)
            print(f"{owner.name} 将 {self.name} 放入战场")

        # 触发技能
        self.activate_skills(owner=owner, board=board)

    def info(self):
        """
        返回卡牌信息，用于 UI 渲染或调试
        """
        return {
            "name": self.name,
            "points": self.points,
            "skills": [str(skill) for skill in self.skills],
            "is_isolated": self.is_isolated
        }

    def __str__(self):
        return f"Card({self.name}, points={self.points}, isolated={self.is_isolated})"

