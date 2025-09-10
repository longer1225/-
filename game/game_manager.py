import random
import pygame
from .board import Board
from .card_factory import create_card_by_number
from .play_action import PlayAction
from ui.constants import END_TURN, PLAY_CARD, SELECT_TARGET

class GameManager:
    def __init__(self, players, total_rounds=3):
        self.players = players
        self.total_rounds = total_rounds
        self.current_round = 0
        self.board = None
        self.current_player_index = 0
        self.reset_scores()  # 初始化得分记录

    def reset_scores(self):
        """重置玩家得分记录"""
        self.small_rounds_won = {p.name: 0 for p in self.players}
        print(f"初始化玩家得分: {self.small_rounds_won}")

    def setup_board(self):
        """初始化战场"""
        self.board = Board(self.players)
        self.reset_scores()  # 设置战场时重置得分

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

    def draw_card_for_player(self, player):
        """为指定玩家抽一张牌"""
        card_number = random.randint(1, 19)
        card = create_card_by_number(card_number)
        return card

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

            # --- 阶段 1：等待玩家行动（选牌或结束回合） ---
            result = ui.wait_for_player_action(player)
            
            # 如果玩家选择结束回合
            if result["type"] == END_TURN:
                players_done[self.current_player_index] = True
                self.next_turn()
                continue
                
            # 如果玩家选择了卡牌
            if result["type"] == PLAY_CARD:
                card = result["card"]
                # 直接使用 UI 返回的选择（防止被重置而丢失）
                targets = result.get("targets", [])
                enemies = result.get("enemies", [])
            else:
                continue

            # --- 阶段 2：选择目标（阻塞等待） ---
            targets, enemies = [], []
            if card.requires_target or card.requires_enemy:
                message = []
                if card.requires_target:
                    message.append("选择目标卡牌")
                if card.requires_enemy:
                    message.append("选择敌方玩家")
                ui.show_message(f"{player.name} 请{' 和 '.join(message)}！")
                
                waiting_for_targets = True
                while waiting_for_targets and ui.running:
                    ui.handle_events()   # 处理玩家操作
                    ui.draw_game()       # 刷新 UI
                    pygame.time.wait(50) # 控制帧率

                    if card.requires_enemy and ui.enemy_list:
                        enemies = ui.enemy_list
                        if not card.requires_target:
                            waiting_for_targets = False
                    
                    if card.requires_target and ui.target_list:
                        targets = ui.target_list
                        if not card.requires_enemy:
                            waiting_for_targets = False
                    
                    if (not card.requires_target or targets) and (not card.requires_enemy or enemies):
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
                enemies=enemies,
                ui=ui
            )
            player.play_card(action)
            # 出牌后切换玩家
            self.next_turn()



        # 小局全部玩家回合结束后结算
        winners = self.end_small_round()
        return winners


    def end_small_round(self):
        """结算小局得分"""
        # 计算并打印所有玩家得分
        scores = {p.name: p.calculate_score() for p in self.players}
        print(f"小局得分: {scores}")

        # 找出最高分
        max_score = max(scores.values())
        winners = [p for p in self.players if p.score == max_score]

        # 更新玩家的胜负状态
        for p in self.players:
            p.prev_round_won = (p in winners)

        # 确保所有玩家都在small_rounds_won中
        for p in self.players:
            if p.name not in self.small_rounds_won:
                print(f"修复: 添加 {p.name} 到得分记录")
                self.small_rounds_won[p.name] = 0

        # 处理胜利结果
        if len(winners) == 1:
            winner = winners[0]
            print(f"{winner.name} 赢得本小局！")
            if winner.name in self.small_rounds_won:
                self.small_rounds_won[winner.name] += 1
                winner.wins += 1
            else:
                print(f"错误：{winner.name} 不在得分记录中")
        else:
            print(f"平局！胜者: {[p.name for p in winners]}")
            for w in winners:
                if w.name in self.small_rounds_won:
                    w.wins += 1
                else:
                    print(f"错误：{w.name} 不在得分记录中")

        # 打印当前总战况
        print(f"当前总战况: {self.small_rounds_won}")
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
        self.reset_scores()  # 使用统一的重置得分方法
        for p in self.players:
            p.reset_all()

