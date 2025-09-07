# game/game_manager.py

import random
from .board import Board
from .card_factory import create_card_by_number  # 工厂函数生成卡牌

class GameManager:
    def __init__(self, players=None, total_rounds=3):
        """
        初始化游戏管理器
        :param players: 玩家列表（Player 对象）
        :param total_rounds: 总局数（默认三局两胜）
        """
        self.players = players or []
        self.total_rounds = total_rounds
        self.current_round = 0
        self.board = None  # Board 对象
        self.small_rounds_won = {player.name: 0 for player in self.players}  # 小局胜利记录
        self.current_player_index = 0

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def next_turn(self):
        """切换到下一位玩家"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def setup_board(self):
        """初始化战场"""
        self.board = Board(self.players)

    # ------------------ 发牌 ------------------
    def deal_cards(self):
        """发牌规则：第一小局6张，之后每小局2张"""
        if self.current_round == 1:
            num_cards = 6
        else:
            num_cards = 2

        for player in self.players:
            for _ in range(num_cards):
                card = self.draw_card_for_player(player)
                player.draw_card(card)

    def draw_card_for_player(self, player):
        """从无限牌堆随机生成一张牌"""
        card_number = random.randint(1, 3)  # 示例，假设 1-3 号牌
        card = create_card_by_number(card_number)
        print(f"{player.name} 抽到 {card.name}")
        return card

    # ------------------ 小局结算 ------------------
    def end_round(self):
        """所有玩家结束本轮后计算分数并判定胜者"""
        # 计算每个玩家分数
        for player in self.players:
            player.calculate_score()

        # 找出最高分
        max_score = max(player.score for player in self.players)
        winners = [player for player in self.players if player.score == max_score]

        # 更新胜局数：平局时所有赢家都加一
        for winner in winners:
            winner.wins += 1
            self.small_rounds_won[winner.name] += 1

        # 打印胜者信息
        if len(winners) == 1:
            print(f"{winners[0].name} 赢得本小局！")
        else:
            print(f"本小局平局，胜者: {[p.name for p in winners]}")

        # 重置玩家战场和孤立区，为下一轮做准备
        for player in self.players:
            player.reset_board()  # 包括战场、孤立区

        self.current_round += 1
        self.current_player_index = 0


    # ------------------ 大局判定 ------------------
    def determine_big_winner(self):
        """根据小局胜局数判定大局胜者"""
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
            print(f"{player.name} 战场牌: {[c.name for c in player.battlefield]}")
            print(f"{player.name} 孤立牌: {[c.name for c in player.isolated]}")

    def show_winner(self):
        """打印大局胜利者"""
        winners = self.determine_big_winner()
        if len(winners) == 1:
            print(f"大局胜利者是 {winners[0]}！")
        else:
            print(f"大局平局！胜者: {winners}")
