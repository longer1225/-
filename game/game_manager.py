import random
from .board import Board
from .card_factory import create_card_by_number
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
        self.board = None
        self.small_rounds_won = {player.name: 0 for player in players}
        self.current_player_index = 0

    def setup_board(self):
        """初始化战场"""
        self.board = Board(self.players)

    def start_small_round(self):
        """开始小局（发牌 + 重置状态）"""
        self.current_round += 1
        print(f"\n=== 第 {self.current_round} 小局 ===")
        self.deal_cards()
        for player in self.players:
            player.reset_round_state()
        print("小局开始！")

    def end_small_round(self):
        """结算小局"""
        scores = {p.name: p.calculate_score() for p in self.players}
        print(f"小局得分: {scores}")

        max_score = max(scores.values())
        winners = [p for p in self.players if p.score == max_score]

        for p in self.players:
            p.prev_round_won = (p in winners)

        if len(winners) == 1:
            print(f"{winners[0].name} 赢得本小局！")
            self.small_rounds_won[winners[0].name] += 1
            winners[0].wins += 1
        else:
            print(f"平局！胜者: {[p.name for p in winners]}")
            for w in winners:
                w.wins += 1

        return winners

    def deal_cards(self):
        """发牌规则"""
        num_cards = 6 if self.current_round == 1 else 2
        for player in self.players:
            for _ in range(num_cards):
                card = self.draw_card_for_player(player)
                player.draw_card(card)

    def draw_card_for_player(self, player):
        """无限牌堆随机抽牌"""
        card_number = random.randint(1, 10)
        card = create_card_by_number(card_number)
        print(f"{player.name} 抽到 {card.name}")
        return card

    def show_winner(self):
        """大局胜利判定"""
        max_wins = max(self.small_rounds_won.values())
        winners = [name for name, wins in self.small_rounds_won.items() if wins == max_wins]
        return winners

    # ------------------ 游戏重置 ------------------
    def reset_for_new_game(self):
        """重新开始大局"""
        self.current_round = 0
        self.current_player_index = 0
        self.small_rounds_won = {player.name: 0 for player in self.players}
        for player in self.players:
            player.reset_all()

    # ------------------ 调试接口 ------------------
    def show_board(self):
        for player in self.players:
            print(f"{player.name} 手牌: {[c.name for c in player.hand]}")
            print(f"{player.name} 战场牌: {[c.name for c in player.battlefield_cards]}")
            print(f"{player.name} 孤立牌: {[c.name for c in player.isolated_cards]}")

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def next_turn(self):
        """进入下一个玩家回合"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
