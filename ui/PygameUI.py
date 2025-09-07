import pygame
from game.player import Player
from game.game_manager import GameManager
from game.play_action import PlayAction

# ------------------ UI 参数 ------------------
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 30

CARD_WIDTH = 60
CARD_HEIGHT = 90
CARD_MARGIN = 10

ZONE_HEIGHT = 120
ZONE_MARGIN = 40

# 区域颜色
COLOR_BG = (30, 30, 30)
COLOR_ZONE = (60, 60, 100)
COLOR_SELECTED = (200, 200, 50)
COLOR_CURRENT = (100, 150, 250)
COLOR_TEXT = (255, 255, 255)


class PygameUI:
    def __init__(self, game_manager: GameManager):
        pygame.init()
        self.gm = game_manager
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("萝卜昆特牌")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 20)

        # ------------------ 玩家选牌状态 ------------------
        self.selected_card = None        # 当前选中的手牌
        self.selecting_targets = False   # 是否在选技能目标阶段
        self.target_list = []            # 已选择技能目标列表

        self.running = True
        self.state = "menu"              # menu / game
        self.selected_num = None         # 玩家人数选择

        # 游戏按钮
        self.button_play = pygame.Rect(WINDOW_WIDTH - 200, 100, 150, 40)
        self.button_end_turn = pygame.Rect(WINDOW_WIDTH - 200, 160, 150, 40)

        # 当前玩家结束状态
        self.players_done = []

        # 胜利显示
        self.round_winner = None
        self.big_winner = None

        # 控制小局/大局
        self.round_over = False
        self.game_over = False

    # ------------------ 主循环 ------------------
    def run(self):
        while self.running:
            self.handle_events()
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "game":
                self.draw_game()
            self.clock.tick(FPS)

    # ------------------ 事件处理 ------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if self.state == "menu":
                    self.handle_menu_click(x, y)
                elif self.state == "game" and not self.game_over:
                    self.handle_game_click(x, y)

    def handle_game_click(self, x, y):
        current_player = self.gm.current_player

        # -------------------- 点击手牌 --------------------
        clicked_card = self.check_click_card(x, y)
        if clicked_card:
            if self.selected_card == clicked_card:
                self.selected_card = None
                self.target_list = []
            else:
                self.selected_card = clicked_card
                self.target_list = []
            return

        # -------------------- 点击目标牌 --------------------
        target_card = self.check_click_target(x, y)
        if target_card and self.selected_card:
            if target_card in self.target_list:
                self.target_list.remove(target_card)
            else:
                valid = False
                for skill in self.selected_card.skills:
                    if skill.targets_required > 0:
                        if skill.target_type == "self" and target_card in current_player.battlefield + current_player.isolated:
                            valid = True
                        elif skill.target_type == "other":
                            for p in self.gm.players:
                                if p != current_player and target_card in p.battlefield + p.isolated:
                                    valid = True
                if valid:
                    self.target_list.append(target_card)

        # -------------------- 点击出牌按钮 --------------------
        if self.button_play.collidepoint(x, y) and self.selected_card:
            max_targets = max((s.targets_required for s in self.selected_card.skills), default=0)
            if len(self.target_list) >= max_targets:
                action = PlayAction(owner=current_player, self_card=self.selected_card, board=self.gm.board,manager=self.gm)
                for t in self.target_list:
                    action.add_target(t)
                current_player.play_card(action, self.gm.board)
                # 出牌后更新 UI
                if self.selected_card in current_player.hand:
                    current_player.hand.remove(self.selected_card)
                self.selected_card = None
                self.target_list = []

        # -------------------- 点击结束回合按钮 --------------------
        if self.button_end_turn.collidepoint(x, y):
            self.players_done[self.gm.current_player_index] = True
            self.selected_card = None
            self.target_list = []

            if all(self.players_done):
                self.round_over = True
                self.gm.end_round()
                winners = [p.name for p in self.gm.players if p.prev_round_won or p.wins > 0]
                self.round_winner = ", ".join(winners)
                self.players_done = [False] * len(self.gm.players)
                self.gm.current_player_index = 0
            else:
                self.gm.next_turn()

    # ------------------ 菜单点击 ------------------
    def handle_menu_click(self, x, y):
        for i, num in enumerate([2, 3, 4]):
            rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 200 + i * 60, 100, 40)
            if rect.collidepoint(x, y):
                self.selected_num = num

        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 400, 100, 40)
        if start_rect.collidepoint(x, y) and self.selected_num:
            self.gm.players = [Player(f"玩家{i+1}", i) for i in range(self.selected_num)]
            self.gm.setup_board()
            self.gm.deal_cards()
            self.players_done = [False] * len(self.gm.players)
            self.state = "game"

    # ------------------ 菜单绘制 ------------------
    def draw_menu(self):
        self.screen.fill(COLOR_BG)
        title = self.font.render("选择玩家人数", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - 80, 100))
        for i, num in enumerate([2, 3, 4]):
            rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 200 + i * 60, 100, 40)
            color = (100, 200, 100) if self.selected_num == num else (150, 150, 150)
            pygame.draw.rect(self.screen, color, rect)
            text = self.font.render(f"{num} 玩家", True, COLOR_TEXT)
            self.screen.blit(text, (rect.x + 15, rect.y + 10))
        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 400, 100, 40)
        pygame.draw.rect(self.screen, (200, 100, 100), start_rect)
        start_text = self.font.render("开始游戏", True, COLOR_TEXT)
        self.screen.blit(start_text, (start_rect.x + 5, start_rect.y + 10))
        pygame.display.flip()

    # ------------------ 游戏界面 ------------------
    def draw_game(self):
        self.screen.fill(COLOR_BG)
        for idx, player in enumerate(self.gm.players):
            is_current = (idx == self.gm.current_player_index)
            self.draw_player_zones(player, idx, highlight=is_current)

        pygame.draw.rect(self.screen, (100, 200, 100), self.button_play)
        self.screen.blit(self.font.render("出牌", True, COLOR_TEXT),
                         (self.button_play.x + 40, self.button_play.y + 10))
        pygame.draw.rect(self.screen, (200, 100, 100), self.button_end_turn)
        self.screen.blit(self.font.render("结束回合", True, COLOR_TEXT),
                         (self.button_end_turn.x + 20, self.button_end_turn.y + 10))

        if self.round_winner:
            winner_text = self.font.render(f"本小局胜者: {self.round_winner}", True, (255, 255, 0))
            self.screen.blit(winner_text, (WINDOW_WIDTH // 2 - 80, 50))

        if any(p.wins >= 2 for p in self.gm.players) and not self.game_over:
            self.game_over = True
            max_wins = max(p.wins for p in self.gm.players)
            winners = [p.name for p in self.gm.players if p.wins == max_wins]
            self.big_winner = ", ".join(winners)

        if self.big_winner:
            big_text = self.font.render(f"大局胜者: {self.big_winner}", True, (255, 200, 0))
            self.screen.blit(big_text, (WINDOW_WIDTH // 2 - 80, 20))

        pygame.display.flip()

    # ------------------ 玩家区域绘制 ------------------
    def draw_player_zones(self, player, idx, highlight=False):
        base_y = 50 + idx * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        border_color = COLOR_CURRENT if highlight else COLOR_ZONE
        pygame.draw.rect(self.screen, border_color, (140, base_y - 30, WINDOW_WIDTH - 280, ZONE_HEIGHT * 3 + 30), 2)
        self.draw_zone("手牌", player.hand, idx, "hand", base_y)
        self.draw_zone("战场", player.battlefield, idx, "battlefield", base_y + ZONE_HEIGHT + 10)
        self.draw_zone("孤立", player.isolated, idx, "isolated", base_y + (ZONE_HEIGHT + 10) * 2)
        info_text = f"{player.name}  分数: {player.score}  胜局: {player.wins}"
        name_text = self.font.render(info_text, True, COLOR_TEXT)
        self.screen.blit(name_text, (20, base_y - 50))

    def draw_zone(self, label, cards, player_index, zone_type, y):
        pygame.draw.rect(self.screen, COLOR_ZONE, (150, y, WINDOW_WIDTH - 400, ZONE_HEIGHT), 2)
        text = self.font.render(label, True, COLOR_TEXT)
        self.screen.blit(text, (160, y - 20))
        for i, card in enumerate(cards):
            rect = self.get_card_rect(i, player_index, zone_type, y)
            color = COLOR_SELECTED if card == self.selected_card else (180, 180, 180)
            pygame.draw.rect(self.screen, color, rect)
            text = self.font.render(card.name, True, (0, 0, 0))
            self.screen.blit(text, (rect.x + 5, rect.y + 5))

    def check_click_card(self, x, y):
        current_player = self.gm.current_player
        for i, card in enumerate(current_player.hand):
            rect = self.get_card_rect(i, current_player.index, "hand")
            if rect.collidepoint(x, y):
                return card
        return None

    def check_click_target(self, x, y):
        for player in self.gm.players:
            for zone in [player.battlefield, player.isolated]:
                for card in zone:
                    rect = self.get_card_rect_for_target(card, player)
                    if rect.collidepoint(x, y):
                        return card
        return None

    def get_card_rect(self, i, player_index, zone_type, y=None):
        if zone_type == "hand":
            base_y = 50 + player_index * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        elif zone_type == "battlefield":
            base_y = 50 + player_index * (ZONE_HEIGHT * 3 + ZONE_MARGIN) + ZONE_HEIGHT + 10
        elif zone_type == "isolated":
            base_y = 50 + player_index * (ZONE_HEIGHT * 3 + ZONE_MARGIN) + (ZONE_HEIGHT + 10) * 2
        else:
            base_y = y or 0
        x = 200 + i * (CARD_WIDTH + CARD_MARGIN)
        return pygame.Rect(x, base_y + 20, CARD_WIDTH, CARD_HEIGHT)

    def get_card_rect_for_target(self, card, player):
        if card in player.hand:
            zone_type = "hand"
            idx = player.hand.index(card)
        elif card in player.battlefield:
            zone_type = "battlefield"
            idx = player.battlefield.index(card)
        else:
            zone_type = "isolated"
            idx = player.isolated.index(card)
        base_y = 50 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        if zone_type == "battlefield":
            base_y += ZONE_HEIGHT + 10
        elif zone_type == "isolated":
            base_y += (ZONE_HEIGHT + 10) * 2
        x = 200 + idx * (CARD_WIDTH + CARD_MARGIN)
        return pygame.Rect(x, base_y + 20, CARD_WIDTH, CARD_HEIGHT)
