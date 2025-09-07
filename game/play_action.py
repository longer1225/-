# game/play_action.py

class PlayAction:
    def __init__(self, owner, self_card, board):
        """
        封装一次出牌的完整上下文
        :param owner: 出牌的玩家对象
        :param self_card: 要出的卡牌对象
        :param board: 游戏的 Board 对象
        """
        self.owner = owner
        self.self_card = self_card
        self.board = board
        self.targets = []  # 技能作用目标（可以是单个或多个）

    def add_target(self, target):
        """添加一个目标（UI 点击时调用）"""
        self.targets.append(target)

    def clear_targets(self):
        """清空目标"""
        self.targets.clear()

    def is_ready(self, skill):
        """
        判断是否已经收集到技能所需的目标
        """
        return len(self.targets) >= skill.targets_required

    def to_dict(self):
        """方便调试或网络传输"""
        return {
            "owner": self.owner.name if self.owner else None,
            "card": self.self_card.name if self.self_card else None,
            "targets": [getattr(t, "name", str(t)) for t in self.targets]
        }

    def __repr__(self):
        return f"<PlayAction owner={self.owner.name}, card={self.self_card.name}, targets={[t.name for t in self.targets]}>"
