class Player:
    def __init__(self, name):
        """
        初始化玩家
        :param name: 玩家名字
        """
        self.name = name
        self.hand = []           # 手牌列表（Card 对象）
        self.board_cards = []    # 场上牌列表
        self.isolated_cards = [] # 孤立牌列表
        self.score = 0           # 玩家分数
        self.prev_round_won = False  # 上一小局是否获胜

    def draw_card(self, card):
        """
        玩家抽一张牌加入手牌
        """
        self.hand.append(card)
        print(f"{self.name} 抽到卡牌 {card.name}")

    def play_card(self, card, board, ui_manager):
        if card not in self.hand:
            print(f"{self.name} 没有这张卡牌 {card.name}")
            return

        self.hand.remove(card)

        # 询问 UIManager：技能是否需要目标
        target_card, targets = None, None
        if card.skills:
            for skill in card.skills:
                if skill.needs_target:
                    target_card = ui_manager.get_target_card(board)
                elif skill.needs_multiple_targets:
                    targets = ui_manager.get_targets(board)

        # 出牌 + 技能触发
        card.play(owner=self, board=board, target_card=target_card, targets=targets)


        # 自动更新玩家自己的战场/孤立区记录
        if card.is_isolated:
            self.isolated_cards.append(card)
        else:
            self.board_cards.append(card)

    def calculate_score(self):
        """
        计算当前分数：战场牌 + 孤立牌点数之和
        """
        total = sum(card.points for card in self.board_cards + self.isolated_cards)
        self.score = total
        return self.score

    def show_hand(self):
        """
        打印手牌信息
        """
        print(f"{self.name} 的手牌: {[card.name for card in self.hand]}")

    def show_board(self):
        """
        打印战场牌信息
        """
        print(f"{self.name} 的战场牌: {[card.name for card in self.board_cards]}")

    def show_isolated(self):
        """
        打印孤立牌信息
        """
        print(f"{self.name} 的孤立牌: {[card.name for card in self.isolated_cards]}")
