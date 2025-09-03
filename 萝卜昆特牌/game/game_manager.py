# game/game_manager.py

import random
from card_factory import create_card_by_number  # 工厂函数生成卡牌

class GameManager:
    def __init__(self, players, total_rounds=3):
        """
        初始化游戏管理器
        :param players: 玩家列表（Player 对象）
        :param total_rounds: 总局数（默认三局两胜）
        """
        self.players = players
        self.total_rounds = total_rounds
        self.current_round = 0
        self.board = None  # Board 对象，稍后初始化
        self.small_rounds_won = {player.name: 0 for player in players}  # 小局胜利记录

    def setup_board(self):
        """
        初始化战场
        """
        from board import Board
        self.board = Board(self.players)

    def start_game(self):
        """
        游戏主流程
        """
        self.setup_board()
        print("游戏开始！")
        self.play_game()

    def play_game(self):
        """
        控制大局（total_rounds）循环
        """
        while max(self.small_rounds_won.values()) < (self.total_rounds // 2 + 1):
            self.current_round += 1
            print(f"=== 第 {self.current_round} 小局 ===")
            self.play_small_round()

        self.show_winner()

    def play_small_round(self):
        """
        小局流程：
        1. 发牌（第一小局发6张，之后每小局发2张）
        2. 玩家轮流出牌
        3. 小局计分
        """
        self.deal_cards()
        # TODO: 玩家轮流出牌逻辑，可以通过 UI 或命令行触发 play_card()
        # 这里先留空或用模拟逻辑

        # 计算小局分数
        scores = {player.name: player.calculate_score() for player in self.players}
        print(f"小局得分: {scores}")
        # 判定小局胜利者
        winner = max(scores, key=scores.get)
        self.small_rounds_won[winner] += 1
        print(f"{winner} 赢得本小局！")

    def deal_cards(self):
        """
        发牌规则：
        - 第一小局每人发6张牌
        - 之后每小局每人发2张牌
        """
        if self.current_round == 1:
            num_cards = 6
        else:
            num_cards = 2

        for player in self.players:
            for _ in range(num_cards):
                card_number = random.randint(1, 20)  # 假设有1-20号牌
                card = create_card_by_number(card_number)
                player.draw_card(card)

    def show_winner(self):
        """
        大局胜利判定
        """
        max_wins = max(self.small_rounds_won.values())
        winners = [name for name, wins in self.small_rounds_won.items() if wins == max_wins]
        if len(winners) == 1:
            print(f"大局胜利者是 {winners[0]}！")
        else:
            print(f"大局平局！胜者: {winners}")

    def show_board(self):
        """
        调试/渲染接口
        """
        if self.board:
            self.board.show_board()
