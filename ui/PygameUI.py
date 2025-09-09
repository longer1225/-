import pygame

# ------------------ UI 参数 ------------------
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 30

CARD_WIDTH = 60
CARD_HEIGHT = 90
CARD_MARGIN = 10

ZONE_HEIGHT = 120
ZONE_MARGIN = 40

COLOR_BG = (30, 30, 30)
COLOR_ZONE = (60, 60, 100)
COLOR_SELECTED = (200, 200, 50)
COLOR_CURRENT = (100, 150, 250)
COLOR_TEXT = (255, 255, 255)
COLOR_TOOLTIP_BG = (50, 50, 70)
COLOR_TOOLTIP_BORDER = (100, 100, 150)


class PygameUI:
    """状态驱动 UI，只负责绘制和输入参数，不处理游戏逻辑"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("萝卜昆特牌")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 20)
        self.small_font = pygame.font.SysFont("simhei", 16)

        # 状态
        self.running = True
        self.state = "menu"  # menu / game
        self.selected_num = None  # 菜单选择人数

        # 游戏参数（外部GameManager会填充）
        self.players = []  # 玩家列表
        self.current_player_index = 0
        self.turn_number = 1
        self.round_winner = None
        self.big_winner = None

        # 玩家选择状态
        self.selected_card = None
        self.selecting_targets = False
        self.target_list = []
        self.enemy_list = []

        # 鼠标悬停
        self.hovered_card = None

        # 控制帮助界面
        self.show_help = False

        # 按钮
        self.button_play = pygame.Rect(WINDOW_WIDTH - 200, 100, 150, 40)
        self.button_end_turn = pygame.Rect(WINDOW_WIDTH - 200, 160, 150, 40)
        self.button_help = pygame.Rect(WINDOW_WIDTH - 200, 220, 150, 40)

        # UI 返回操作
        self.action_result = None  # {'type': 'select_card' / 'play' / 'end_turn', ...}

    # ------------------ 主循环 ------------------
    def run(self):
        while self.running:
            self.handle_events()
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "game":
                self.draw_game()
            self.clock.tick(FPS)
            yield self.action_result
            self.action_result = None

    # ------------------ 事件处理 ------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.action_result = {"type": "quit"}
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if self.state == "menu":
                    self.handle_menu_click(x, y)
                elif self.state == "game":
                    self.handle_game_click(x, y)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_ESCAPE:
                    if self.show_help:
                        self.show_help = False
                    elif self.selected_card:
                        self.selected_card = None
                        self.target_list = []
                        self.enemy_list = []

    def handle_mouse_motion(self, pos):
        x, y = pos
        self.hovered_card = None
        if self.state != "game":
            return
        current_player = self.players[self.current_player_index]
        for card in current_player.hand:
            rect = self.get_card_rect_for_card(card, current_player)
            if rect.collidepoint(x, y):
                self.hovered_card = card
                return
        for player in self.players:
            for zone in [player.get("battlefield_cards", []), player.get("isolated_cards", [])]:
                for card in zone:
                    rect = self.get_card_rect_for_card(card, player)
                    if rect.collidepoint(x, y):
                        self.hovered_card = card
                        return

    # ------------------ 菜单点击 ------------------
    def handle_menu_click(self, x, y):
        # 玩家人数选择
        for i, num in enumerate([2, 3, 4]):
            rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 200 + i * 60, 100, 40)
            if rect.collidepoint(x, y):
                self.selected_num = num

        # 开始游戏按钮
        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 400, 100, 40)
        if start_rect.collidepoint(x, y) and self.selected_num:
            # 创建玩家列表
            self.gm.players = [Player(f"玩家{i+1}", i) for i in range(self.selected_num)]
            # 初始化游戏板和发牌
            self.gm.setup_board()
            self.gm.deal_cards()
            # 初始化玩家结束状态
            self.players_done = [False] * len(self.gm.players)
            # 切换到游戏界面
            self.state = "game"


    # ------------------ 游戏点击 ------------------
    def handle_game_click(self, x, y):
        # 点击手牌
        clicked_card = self.check_click_card(x, y)
        if clicked_card:
            self.selected_card = clicked_card if clicked_card != self.selected_card else None
            self.target_list = []
            self.enemy_list = []
            self.selecting_targets = getattr(clicked_card, 'requires_target', False)
            self.action_result = {"type": "select_card", "card": self.selected_card}
            return

        # 点击目标或敌人
        target_card = self.check_click_target(x, y)
        if target_card and self.selected_card and self.selecting_targets:
            if target_card in self.target_list:
                self.target_list.remove(target_card)
            else:
                self.target_list.append(target_card)
            self.action_result = {"type": "select_targets", "targets": self.target_list}

        target_enemy = self.check_click_enemy(x, y)
        if target_enemy and self.selected_card and self.selecting_targets:
            if target_enemy in self.enemy_list:
                self.enemy_list.remove(target_enemy)
            else:
                self.enemy_list.append(target_enemy)
            self.action_result = {"type": "select_enemies", "enemies": self.enemy_list}

        # 点击出牌/结束回合
        if self.button_play.collidepoint(x, y) and self.selected_card:
            self.action_result = {"type": "play_card", "card": self.selected_card,
                                  "targets": self.target_list, "enemies": self.enemy_list}
            self.selected_card = None
            self.target_list = []
            self.enemy_list = []
            self.selecting_targets = False

        if self.button_end_turn.collidepoint(x, y):
            self.action_result = {"type": "end_turn"}

        if self.button_help.collidepoint(x, y):
            self.show_help = not self.show_help

    # ------------------ 绘制 ------------------
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
        help_text = self.small_font.render("按 H 键查看游戏帮助", True, COLOR_TEXT)
        self.screen.blit(help_text, (WINDOW_WIDTH // 2 - 80, 500))
        pygame.display.flip()

    def draw_game(self):
        self.screen.fill(COLOR_BG)
        if self.show_help:
            self.draw_help_screen()
            pygame.display.flip()
            return
        # 绘制玩家区域
        for idx, player in enumerate(self.players):
            is_current = idx == self.current_player_index
            self.draw_player_zones(player, idx, highlight=is_current)

        # 按钮
        pygame.draw.rect(self.screen, (100, 200, 100), self.button_play)
        self.screen.blit(self.font.render("出牌", True, COLOR_TEXT),
                         (self.button_play.x + 40, self.button_play.y + 10))
        pygame.draw.rect(self.screen, (200, 100, 100), self.button_end_turn)
        self.screen.blit(self.font.render("结束回合", True, COLOR_TEXT),
                         (self.button_end_turn.x + 20, self.button_end_turn.y + 10))
        pygame.draw.rect(self.screen, (100, 100, 200), self.button_help)
        self.screen.blit(self.font.render("帮助", True, COLOR_TEXT),
                         (self.button_help.x + 40, self.button_help.y + 10))
        # 回合信息
        phase_text = self.font.render(f"回合: {self.turn_number}", True, COLOR_TEXT)
        self.screen.blit(phase_text, (WINDOW_WIDTH - 250, 20))
        # 小局/大局胜者
        if self.round_winner:
            winner_text = self.font.render(f"本小局胜者: {self.round_winner}", True, (255, 255, 0))
            self.screen.blit(winner_text, (WINDOW_WIDTH // 2 - 80, 50))
        if self.big_winner:
            big_text = self.font.render(f"大局胜者: {self.big_winner}", True, (255, 200, 0))
            self.screen.blit(big_text, (WINDOW_WIDTH // 2 - 80, 20))
        # 悬停提示
        if self.hovered_card:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.draw_card_tooltip(self.hovered_card, mouse_x + 20, mouse_y + 20)
        pygame.display.flip()

    def draw_help_screen(self):
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.screen.blit(s, (0, 0))
        title = self.font.render("游戏帮助", True, (255, 255, 0))
        self.screen.blit(title, (WINDOW_WIDTH // 2 - 50, 50))
        help_lines = [
            "- 点击卡牌选择/取消选择",
            "- 点击目标区域选择技能目标",
            "- 点击'出牌'按钮打出选中卡牌",
            "- 点击'结束回合'按钮结束当前回合",
            "- H: 显示/隐藏帮助",
            "- ESC: 取消选择/关闭帮助"
        ]
        for i, line in enumerate(help_lines):
            text = self.small_font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (WINDOW_WIDTH // 2 - 200, 100 + i * 25))

    # ------------------ 玩家区域 ------------------
    def draw_player_zones(self, player, idx, highlight=False):
        base_y = 50 + idx * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        border_color = COLOR_CURRENT if highlight else COLOR_ZONE
        pygame.draw.rect(self.screen, border_color, (140, base_y - 30, WINDOW_WIDTH - 280, ZONE_HEIGHT * 3 + 30), 2)
        self.draw_zone("手牌", player.get("hand", []), idx, "hand", base_y)
        self.draw_zone("战场", player.get("battlefield_cards", []), idx, "battlefield", base_y + ZONE_HEIGHT + 10)
        self.draw_zone("孤立", player.get("isolated_cards", []), idx, "isolated", base_y + (ZONE_HEIGHT + 10) * 2)
        info_text = f"{player.get('name', '')}  分数: {player.get('score', 0)}  胜局: {player.get('wins', 0)}"
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
            text = self.font.render(getattr(card, 'name', str(card)), True, (0, 0, 0))
            self.screen.blit(text, (rect.x + 5, rect.y + 5))

    # ------------------ 点击检测 ------------------
    def check_click_card(self, x, y):
        current_player = self.players[self.current_player_index]
        for card in current_player.get("hand", []):
            rect = self.get_card_rect_for_card(card, current_player)
            if rect.collidepoint(x, y):
                return card
        return None

    def check_click_target(self, x, y):
        for player in self.players:
            for zone in [player.get("hand", []), player.get("battlefield_cards", []), player.get("isolated_cards", [])]:
                for card in zone:
                    rect = self.get_card_rect_for_card(card, player)
                    if rect.collidepoint(x, y):
                        return card
        return None

    def check_click_enemy(self, x, y):
        for idx, player in enumerate(self.players):
            base_y = 50 + idx * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
            avatar_rect = pygame.Rect(20, base_y - 50, 100, 100)
            if avatar_rect.collidepoint(x, y):
                return player
        return None

    # ------------------ 卡牌位置 ------------------
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

    def get_card_rect_for_card(self, card, player):
        if card in player.get("hand", []):
            zone_type = "hand"
            idx = player["hand"].index(card)
        elif card in player.get("battlefield_cards", []):
            zone_type = "battlefield"
            idx = player["battlefield_cards"].index(card)
        else:
            zone_type = "isolated"
            idx = player.get("isolated_cards", []).index(card)
        base_y = 50 + self.players.index(player) * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        if zone_type == "battlefield":
            base_y += ZONE_HEIGHT + 10
        elif zone_type == "isolated":
            base_y += (ZONE_HEIGHT + 10) * 2
        x = 200 + idx * (CARD_WIDTH + CARD_MARGIN)
        return pygame.Rect(x, base_y + 20, CARD_WIDTH, CARD_HEIGHT)

    # ------------------ 卡牌悬停提示 ------------------
    def draw_card_tooltip(self, card, x, y):
        description = getattr(card, 'description', '暂无描述')
        lines = self.wrap_text(description, 180)
        height = 60 + len(lines) * 20
        if x + 210 > WINDOW_WIDTH:
            x = WINDOW_WIDTH - 210
        if y + height > WINDOW_HEIGHT:
            y = WINDOW_HEIGHT - height
        tooltip_rect = pygame.Rect(x, y, 200, height)
        pygame.draw.rect(self.screen, COLOR_TOOLTIP_BG, tooltip_rect)
        pygame.draw.rect(self.screen, COLOR_TOOLTIP_BORDER, tooltip_rect, 2)
        name_text = self.font.render(getattr(card, 'name', str(card)), True, (255, 255, 255))
        self.screen.blit(name_text, (x + 10, y + 10))
        for i, line in enumerate(lines):
            desc_text = self.small_font.render(line, True, (200, 200, 200))
            self.screen.blit(desc_text, (x + 10, y + 40 + i * 20))

    # ------------------ 文本换行 ------------------
    def wrap_text(self, text, max_width):
        lines = []
        if not text:
            return lines
        words = text.split(' ')
        current_line = ''
        for word in words:
            test_line = current_line + (' ' if current_line else '') + word
            if self.font.size(test_line)[0] > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
        return lines
