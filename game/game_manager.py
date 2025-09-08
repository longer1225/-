# game/game_manager.py

import random
from .board import Board
from .card_factory import create_card_by_number  # 工厂函数生成卡牌
import sys
sys.stdout.reconfigure(encoding='utf-8')

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
            print(f"\n=== 第 {self.current_round} 小局 ===")
            self.play_small_round()

        self.show_winner()

    def play_small_round(self):
        """
        小局流程：
        1. 发牌
        2. 玩家轮流出牌（由 UI 或事件控制）
        3. 小局计分
        """
        self.deal_cards()

        # TODO: 玩家轮流出牌逻辑，由 UI 或交互事件触发 Player.play_card()

        # 计算小局分数
        scores = {player.name: player.calculate_score() for player in self.players}
        print(f"小局得分: {scores}")

        # 判定小局胜利者
        max_score = max(scores.values())
        winners = [player for player in self.players if player.score == max_score]

        # 更新每个玩家的上一小局胜负状态
        for player in self.players:
            player.prev_round_won = player in winners

        # 打印胜者
        if len(winners) == 1:
            print(f"{winners[0].name} 赢得本小局！")
            self.small_rounds_won[winners[0].name] += 1
        else:
            print(f"本小局平局，胜者: {[p.name for p in winners]}")

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
                card = self.draw_card_for_player(player)
                player.draw_card(card)

    def draw_card_for_player(self, player):
        """
        无限牌堆：每次随机生成一张牌
        """
        card_number = random.randint(1, 20)  # 假设有 1-20 号牌
        card = create_card_by_number(card_number)
        print(f"{player.name} 抽到 {card.name}")
        return card

    def show_winner(self):
        """
        大局胜利判定
        """
        max_wins = max(self.small_rounds_won.values())
        winners = [name for name, wins in self.small_rounds_won.items() if wins == max_wins]
        return winners  # 返回列表，由前端显示

    # ------------------ 游戏重置 ------------------
    def reset_for_new_game(self):
        """重新开始大局"""
        self.current_round = 0
        self.current_player_index = 0
        self.small_rounds_won = {player.name: 0 for player in self.players}
        for player in self.players:
            player.reset_all()  # 包括手牌、战场、孤立区、分数、胜局数

    # ------------------ 调试/渲染接口 ------------------
    def show_board(self):
        for player in self.players:
            print(f"{player.name} 手牌: {[c.name for c in player.hand]}")
            print(f"{player.name} 战场牌: {[c.name for c in player.battlefield_cards]}")
            print(f"{player.name} 孤立牌: {[c.name for c in player.isolated_cards]}")


    def show_board(self):
        """
        调试/渲染接口
        """
        for player in self.players:
            print(f"{player.name} 手牌: {[c.name for c in player.hand]}")
            print(f"{player.name} 战场牌: {[c.name for c in player.board_cards]}")
            print(f"{player.name} 孤立牌: {[c.name for c in player.isolated_cards]}")
