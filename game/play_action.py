# >>> CHANGED: 新增 PlayAction，包含 manager 和 enemies（方便技能调用游戏管理器或选敌人）
class PlayAction:
    def __init__(self, owner, self_card, board, manager, targets, enemies=None):
        """
        :param owner: 出牌玩家
        :param self_card: 被出的卡牌
        :param board: Board 对象
        :param manager: GameManager（可选，许多技能需要调用 draw_card 等方法）
        :param targets: 卡牌目标列表（通常是牌对象）
        :param enemies: 敌方玩家列表（通常是 Player 对象）
        """
        self.owner = owner
        self.self_card = self_card
        self.board = board
        self.manager = manager
        self.targets = targets or []
        self.enemies = enemies or []


    def add_target(self, t):
        self.targets.append(t)


    def add_enemy(self, e):
        self.enemies.append(e)


    def clear_targets(self):
        self.targets.clear()
        self.enemies.clear()


    def to_dict(self):
        return {
        "owner": self.owner.name if self.owner else None,
        "card": self.self_card.name if self.self_card else None,
        "targets": [getattr(t, "name", str(t)) for t in self.targets],
        "enemies": [getattr(e, "name", str(e)) for e in self.enemies],
        }