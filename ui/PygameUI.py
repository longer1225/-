import pygame
import sys
from game.player import Player

# 常量定义
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
ZONE_WIDTH = 200
ZONE_HEIGHT = 100
ZONE_MARGIN = 20

COLOR_BG = (30, 30, 30)
COLOR_ZONE = (60, 60, 60)
COLOR_TEXT = (220, 220, 220)
COLOR_HIGHLIGHT = (100, 100, 200)
COLOR_CURRENT = (200, 200, 100)

class PygameUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("萝卜昆特牌")

        self.font = pygame.font.SysFont("simhei", 24)
        self.clock = pygame.time.Clock()

        # 状态：菜单 or 游戏
        self.state = "menu"
        self.selected_num = None

        # Manager 绑定
        self.gm = None

        # 游戏状态
        self.players = []
        self.current_player_index = 0
        self.players_done = []
        self.action_result = None

    # ========== 外部交互接口 ==========
    def set_manager(self, gm):
        self.gm = gm

    def wait_for_player_action(self, player):
        """等待玩家操作，返回 action_result"""
        self.action_result = None
        while self.action_result is None:
            self.handle_events()
            self.draw()
            self.clock.tick(30)
        return self.action_result

    def player_end_turn(self, player):
        """等待玩家点击“结束回合”"""
        self.action_result = None
        while self.action_result is None:
            self.handle_events()
            self.draw()
            self.clock.tick(30)
        return self.action_result

    # ========== 事件处理 ==========
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if self.state == "menu":
                    self.handle_menu_click(x, y)
                elif self.state == "game":
                    self.handle_game_click(x, y)

            elif event.type == pygame.MOUSEMOTION and self.state == "game":
                self.handle_mouse_motion(event.pos)

    def handle_menu_click(self, x, y):
        # 选择人数
        for i, num in enumerate([2, 3, 4]):
            rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 200 + i * 60, 100, 40)
            if rect.collidepoint(x, y):
                self.selected_num = num

        # 开始游戏
        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 400, 100, 40)
        if start_rect.collidepoint(x, y) and self.selected_num:
            # 由 UI 负责初始化玩家
            self.gm.players = [Player(f"玩家{i+1}", i) for i in range(self.selected_num)]
            self.gm.setup_board()
            self.gm.deal_cards()

            self.players = self.gm.players
            self.players_done = [False] * len(self.gm.players)

            self.state = "game"

    def handle_game_click(self, x, y):
        current_player = self.players[self.current_player_index]

        # 点击卡牌
        clicked_card = self.check_click_card(current_player, x, y)
        if clicked_card:
            self.action_result = {"action": "play_card", "card": clicked_card}
            return

        # 点击敌人目标
        clicked_target = self.check_click_target(current_player, x, y)
        if clicked_target:
            self.action_result = {"action": "select_target", "target": clicked_target}
            return

        # 点击结束回合按钮
        end_turn_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 60, 120, 40)
        if end_turn_rect.collidepoint(x, y):
            self.action_result = {"action": "end_turn"}
            return

    def handle_mouse_motion(self, pos):
        x, y = pos
        current_player = self.players[self.current_player_index]
        for card in current_player.hand:
            rect = self.get_card_rect_for_card(card, current_player)
            if rect and rect.collidepoint(x, y):
                card.highlight = True
            else:
                card.highlight = False

    # ========== 绘制 ==========
    def draw(self):
        self.screen.fill(COLOR_BG)
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "game":
            self.draw_game()
        pygame.display.flip()

    def draw_menu(self):
        title = self.font.render("请选择玩家人数", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - 100, 100))

        for i, num in enumerate([2, 3, 4]):
            rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 200 + i * 60, 100, 40)
            pygame.draw.rect(self.screen, COLOR_ZONE, rect)
            label = self.font.render(f"{num}人", True, COLOR_TEXT)
            self.screen.blit(label, (rect.x + 20, rect.y + 5))

        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 400, 100, 40)
        pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, start_rect)
        label = self.font.render("开始游戏", True, COLOR_TEXT)
        self.screen.blit(label, (start_rect.x + 5, start_rect.y + 5))

    def draw_game(self):
        for idx, player in enumerate(self.players):
            self.draw_player_zones(player, idx, idx == self.current_player_index)

        end_turn_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 60, 120, 40)
        pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, end_turn_rect)
        label = self.font.render("结束回合", True, COLOR_TEXT)
        self.screen.blit(label, (end_turn_rect.x + 10, end_turn_rect.y + 5))

    def draw_player_zones(self, player, idx, highlight=False):
        base_y = 50 + idx * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        border_color = COLOR_CURRENT if highlight else COLOR_ZONE
        pygame.draw.rect(self.screen, border_color,
                         (140, base_y - 30, WINDOW_WIDTH - 280, ZONE_HEIGHT * 3 + 30), 2)

        self.draw_zone("手牌", player.hand, idx, "hand", base_y)
        self.draw_zone("战场", player.battlefield_cards, idx, "battlefield", base_y + ZONE_HEIGHT + 10)
        self.draw_zone("孤立", player.isolated_cards, idx, "isolated", base_y + (ZONE_HEIGHT + 10) * 2)

        info_text = f"{player.name}  分数: {player.score}  胜局: {player.wins}"
        name_text = self.font.render(info_text, True, COLOR_TEXT)
        self.screen.blit(name_text, (20, base_y - 50))

    def draw_zone(self, label, cards, player_index, zone_name, y):
        title = self.font.render(label, True, COLOR_TEXT)
        self.screen.blit(title, (150, y - 20))

        for i, card in enumerate(cards):
            rect = pygame.Rect(150 + i * (60 + 5), y, 60, 90)
            pygame.draw.rect(self.screen, (100, 100, 100), rect)
            if hasattr(card, "highlight") and card.highlight:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 3)

            card_text = self.font.render(str(card), True, COLOR_TEXT)
            self.screen.blit(card_text, (rect.x + 5, rect.y + 5))

    # ========== 工具函数 ==========
    def check_click_card(self, player, x, y):
        for i, card in enumerate(player.hand):
            rect = pygame.Rect(150 + i * (60 + 5), 50 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN), 60, 90)
            if rect.collidepoint(x, y):
                return card
        return None

    def check_click_target(self, current_player, x, y):
        for player in self.players:
            if player == current_player:
                continue
            rect = pygame.Rect(140, 50 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN) - 30,
                               WINDOW_WIDTH - 280, ZONE_HEIGHT * 3 + 30)
            if rect.collidepoint(x, y):
                return player
        return None

    def get_card_rect_for_card(self, card, player):
        for i, c in enumerate(player.hand):
            if c == card:
                return pygame.Rect(150 + i * (60 + 5), 50 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN), 60, 90)
        return None
