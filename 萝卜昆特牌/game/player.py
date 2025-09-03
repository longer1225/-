# game/player.py
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

    def draw_card(self, card):
        """
        玩家抽一张牌加入手牌
        """
        self.hand.append(card)
        print(f"{self.name} 抽到卡牌 {card.name}")

    def play_card(self, card, board):
        """
        出牌操作：
        1. 从手牌移除
        2. 放入 Board 的战场或孤立区
        3. 触发技能
        """
        if card not in self.hand:
            print(f"{self.name} 没有这张卡牌 {card.name}")
            return

        self.hand.remove(card)
        card.play(owner=self, board=board)

        # 自动更新场上和孤立区
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
