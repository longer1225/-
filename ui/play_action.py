class PlayAction:
    def __init__(self, player, card):
        """
        用来封装一次出牌的参数
        :param player: 出牌的玩家对象
        :param card: 要出的卡牌对象
        """
        self.player = player
        self.card = card
        self.targets = []  # 技能作用目标（可以是单个或多个）

    def add_target(self, target):
        """添加一个目标"""
        self.targets.append(target)

    def clear_targets(self):
        """清空目标"""
        self.targets.clear()

    def to_dict(self):
        """方便调试或网络传输"""
        return {
            "player": self.player.name if self.player else None,
            "card": self.card.name if self.card else None,
            "targets": [t.name for t in self.targets]
        }