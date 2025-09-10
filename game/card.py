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

        # 计算是否需要目标
        self.requires_target = False
        self.requires_enemy = False
        self.target_type = "none"    # 目标类型：none/hand/battlefield/isolated
        self.target_side = "self"    # 目标方：self/other/any
        
        # 从技能中获取目标要求
        for skill in self.skills:
            if skill.needs_target:
                self.requires_target = True
                self.target_type = skill.target_type
                self.target_side = skill.target_side
            if skill.needs_enemy:
                self.requires_enemy = True

        # UI相关属性
        self.highlight = False  # 用于UI高亮显示

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
            msg = f"{owner.name} 将 {self.name} 放入孤立区"
            if getattr(action, 'ui', None):
                action.ui.add_log(msg)
            else:
                print(msg)
        else:
            owner.battlefield_cards.append(self)
            msg = f"{owner.name} 将 {self.name} 放入战场"
            if getattr(action, 'ui', None):
                action.ui.add_log(msg)
            else:
                print(msg)

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
