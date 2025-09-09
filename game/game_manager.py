import random

import pygame
from .board import Board
from .card_factory import create_card_by_number
import sys
from .play_action import PlayAction
sys.stdout.reconfigure(encoding='utf-8')

class GameManager:
    def __init__(self, players, total_rounds=3):
        self.players = players
        self.total_rounds = total_rounds
        self.current_round = 0
        self.board = None
        self.small_rounds_won = {p.name: 0 for p in players}
        self.current_player_index = 0

    def setup_board(self):
        """初始化战场"""
        self.board = Board(self.players)

    def start_small_round(self):
        """开始小局"""
        self.current_round += 1
        print(f"\n=== 第 {self.current_round} 小局 ===")
        self.deal_cards()
        for player in self.players:
            player.reset_board()
        print("小局开始！")

    def deal_cards(self):
        """发牌规则"""
        num_cards = 6 if self.current_round == 1 else 2
        for player in self.players:
            for _ in range(num_cards):
                card_number = random.randint(1, 10)
                card = create_card_by_number(card_number)
                player.draw_card(card)

    def next_turn(self):
        """下一个玩家回合"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    # ---------------- 小局逻辑 ----------------
    def play_small_round(self, ui):
        """运行一个小局"""
        self.start_small_round()
        self.current_player_index = 0
        players_done = [False] * len(self.players)

        while not all(players_done):
            player = self.current_player
            if players_done[self.current_player_index]:
                self.next_turn()
                continue

            # --- 阶段 0：检查是否直接结束回合 ---
            if ui.player_end_turn(player):
                players_done[self.current_player_index] = True
                self.next_turn()
                continue

            # --- 阶段 1：选择牌 ---
            card = ui.select_card(player)  # 返回 Card 或 None
            if card is None:
                continue

            # --- 阶段 2：选择目标（阻塞等待） ---
            targets, enemies = [], []
            if getattr(card, 'requires_target', False):
                ui.show_message(f"{player.name} 需要选择目标才能出牌！")
                waiting_for_targets = True
                while waiting_for_targets and ui.running:
                    ui.handle_events()   # 处理玩家操作
                    ui.draw_game()       # 刷新 UI
                    pygame.time.wait(50) # 控制帧率

                    if ui.target_list or ui.enemy_list:
                        targets = ui.target_list
                        enemies = ui.enemy_list
                        waiting_for_targets = False

                # 重置选择状态
                ui.selected_card = None
                ui.target_list = []
                ui.enemy_list = []

            # --- 阶段 3：出牌 ---
            action = PlayAction(
                owner=player,
                self_card=card,
                board=self.board,
                manager=self,
                targets=targets,
                enemies=enemies
            )
            player.play_card(action)

            # --- 阶段 4：结束回合检查 ---
            if ui.player_end_turn(player):
                players_done[self.current_player_index] = True
                self.next_turn()

            # 切换到下一玩家
            self.next_turn()

        # 小局全部玩家回合结束后结算
        winners = self.end_small_round()
        return winners


    def end_small_round(self):
        """结算小局得分"""
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

    # ---------------- 大局胜利 ----------------
    def show_winner(self):
        """大局胜利判定"""
        max_wins = max(self.small_rounds_won.values())
        winners = [name for name, wins in self.small_rounds_won.items() if wins == max_wins]
        return winners

    def reset_for_new_game(self):
        """重置大局状态"""
        self.current_round = 0
        self.current_player_index = 0
        self.small_rounds_won = {p.name: 0 for p in self.players}
        for p in self.players:
            p.reset_all()

