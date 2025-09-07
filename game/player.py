# game/player.py
class Player:
    def __init__(self, name, index=0):
        """
        初始化玩家
        :param name: 玩家名字
        :param index: 玩家索引（UI 显示位置用）
        """
        self.name = name
        self.index = index
        self.hand = []            # 手牌列表（Card 对象）
        self.battlefield_cards = []     # 战场牌列表
        self.isolated_cards = []  # 孤立牌列表
        self.score = 0            # 玩家分数
        self.wins=0
        self.prev_round_won = False  # 上一小局是否获胜

    def draw_card(self, card):
        """玩家抽一张牌加入手牌"""
        self.hand.append(card)
        print(f"{self.name} 抽到卡牌 {card.name}")

    def play_card(self, card, board, ui_manager=None):
        """
        出牌：
        1. 从手牌移除
        2. 放入战场或孤立区
        3. 触发技能
        """
        if card not in self.hand:
            print(f"{self.name} 没有这张卡牌 {card.name}")
            return

        self.hand.remove(card)

        # 技能目标处理（交给 UI）
        target_card, targets = None, None
        if ui_manager and card.skills:
            for skill in card.skills:
                if getattr(skill, "targets_required", 0) == 1:
                    target_card = ui_manager.get_target_card(board)
                elif getattr(skill, "targets_required", 0) > 1:
                    targets = ui_manager.get_targets(board)

        # 出牌 + 技能触发
        card.play(owner=self, board=board)

        # 放入对应牌区
        if card.is_isolated:
            self.isolated_cards.append(card)
        else:
            self.battlefield_cards.append(card)

    def calculate_score(self):
        """计算当前分数：战场牌 + 孤立牌点数"""
        total = sum(card.points for card in self.battlefield_cards + self.isolated_cards)
        self.score += total
        return self.score

    # ------- 调试用方法 -------
    def show_hand(self):
        print(f"{self.name} 的手牌: {[card.name for card in self.hand]}")

    def show_board(self):
        print(f"{self.name} 的战场牌: {[card.name for card in self.battlefield_cards]}")

    def show_isolated(self):
        print(f"{self.name} 的孤立牌: {[card.name for card in self.isolated_cards]}")

    @property
    def battlefield(self):

        return self.battlefield_cards

    @property
    def isolated(self):
        return self.isolated_cards


    def reset_all(self):
        """重置玩家手牌、战场、孤立区、分数和胜局数"""
        self.hand.clear()
        self.battlefield.clear()
        self.isolated.clear()
        self.score = 0
        self.wins = 0
        self.prev_round_won = False

    def reset_board(self):
        """重置战场和孤立区，但保留手牌"""
        self.battlefield.clear()
        self.isolated.clear()
        self.score = 0
