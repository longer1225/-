import pygame
import sys
from typing import Optional, Dict, Any, List
from game.player import Player
from game.card import Card
from game.game_manager import GameManager

# 常量定义
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
ZONE_WIDTH = 200
ZONE_HEIGHT = 120
ZONE_MARGIN = 30

COLOR_BG = (30, 30, 40)
COLOR_ZONE = (60, 60, 80)
COLOR_TEXT = (220, 220, 240)
COLOR_HIGHLIGHT = (100, 150, 255)
COLOR_CURRENT = (255, 215, 100)
COLOR_LOG_BG = (40, 40, 55)
COLOR_LOG_BORDER = (80, 80, 120)
COLOR_SCROLLBAR = (100, 100, 150)

# 事件常量
END_TURN = 1
PLAY_CARD = 2
SELECT_TARGET = 3

class PygameUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("萝卜昆特牌")

        # 使用更好的字体
        font_candidates = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
        self.font_large = pygame.font.SysFont(font_candidates, 28)
        self.font_medium = pygame.font.SysFont(font_candidates, 24)
        self.font_small = pygame.font.SysFont(font_candidates, 20)
        self.font_tiny = pygame.font.SysFont(font_candidates, 18)
        
        self.clock = pygame.time.Clock()
        
        # 游戏状态
        self.running: bool = True
        self.state: str = "menu"
        self.selected_num: Optional[int] = None
        self.selected_card: Optional[Card] = None
        self.target_list: List[Player] = []
        self.enemy_list: List[Player] = []
        self.message: str = ""
        self.message_timer: int = 0

        # 日志系统
        self.logs: List[str] = []
        self.log_scroll_offset = 0
        self.max_visible_logs = 8
        self.log_panel_rect = pygame.Rect(20, WINDOW_HEIGHT - 200, WINDOW_WIDTH - 40, 180)
        self.scrollbar_rect = pygame.Rect(WINDOW_WIDTH - 40, WINDOW_HEIGHT - 200, 20, 180)
        self.dragging_scrollbar = False
        self.scrollbar_drag_start = 0

        # Manager 绑定
        self.gm: Optional[GameManager] = None
        
        # 卡牌尺寸
        self.card_width = 90
        self.card_height = 120
        self.card_spacing = 15
        self.card_left = 180

    def set_manager(self, gm: GameManager) -> None:
        """设置游戏管理器"""
        self.gm = gm

    def show_message(self, text: str, duration: int = 2000) -> None:
        """显示消息"""
        self.message = text
        self.message_timer = duration

    def add_log(self, text: str) -> None:
        """添加日志"""
        if not isinstance(text, str):
            text = str(text)
        self.logs.append(text)
        # 自动滚动到最新日志
        self.log_scroll_offset = max(0, len(self.logs) - self.max_visible_logs)

    def select_card(self, player: Player) -> Optional[Card]:
        """等待玩家选择卡牌"""
        self.selected_card = None
        while self.running and self.selected_card is None:
            self.handle_events()
            self.draw_game()
            self.clock.tick(30)
        card = self.selected_card
        self.selected_card = None
        return card

    def wait_for_player_action(self, player: Player) -> Dict[str, Any]:
        """等待玩家操作"""
        waiting = True
        result = {"type": END_TURN}  # 默认结果
        
        while waiting and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # 检查卡牌点击
                    clicked_card = self.check_click_card(player, x, y)
                    if clicked_card:
                        result = {"type": PLAY_CARD, "card": clicked_card}
                        waiting = False
                        break
                    
                    # 检查目标选择
                    clicked_target = self.check_click_target(player, x, y)
                    if clicked_target and self.selected_card:
                        result = {"type": SELECT_TARGET, "target": clicked_target}
                        waiting = False
                        break

                    # 检查结束回合
                    end_turn_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 60, 120, 40)
                    if end_turn_rect.collidepoint(x, y):
                        result = {"type": END_TURN}
                        waiting = False
                        break

                    # 检查日志区域滚动
                    if self.log_panel_rect.collidepoint(x, y):
                        # 处理鼠标滚轮
                        if event.button == 4:  # 向上滚动
                            self.log_scroll_offset = max(0, self.log_scroll_offset - 1)
                        elif event.button == 5:  # 向下滚动
                            max_scroll = max(0, len(self.logs) - self.max_visible_logs)
                            self.log_scroll_offset = min(max_scroll, self.log_scroll_offset + 1)
                        elif event.button == 1:  # 左键点击滚动条
                            if self.scrollbar_rect.collidepoint(x, y):
                                self.dragging_scrollbar = True
                                self.scrollbar_drag_start = y

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging_scrollbar = False
                        
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging_scrollbar:
                        # 根据鼠标拖动位置调整滚动条
                        dy = event.pos[1] - self.scrollbar_drag_start
                        if len(self.logs) > self.max_visible_logs:
                            # 计算滚动比例
                            scroll_ratio = dy / (self.log_panel_rect.height - 40)
                            max_scroll = len(self.logs) - self.max_visible_logs
                            self.log_scroll_offset = max(0, min(max_scroll, int(scroll_ratio * max_scroll)))
                        self.scrollbar_drag_start = event.pos[1]

            self.draw_game()
            self.clock.tick(30)

        return result

    def player_end_turn(self, player: Player) -> bool:
        """检查玩家是否结束回合"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                end_turn_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 60, 120, 40)
                if end_turn_rect.collidepoint(x, y):
                    return True
                
                # 如果点击了卡牌，表示还想继续打牌
                if self.check_click_card(player, x, y):
                    return False
        
        return False

    def handle_events(self) -> None:
        """处理所有事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if self.state == "menu":
                    self.handle_menu_click(x, y)
                elif self.state == "game":
                    self.handle_game_click(x, y)
                    
                # 处理日志滚动
                if self.log_panel_rect.collidepoint(x, y):
                    if event.button == 4:  # 向上滚动
                        self.log_scroll_offset = max(0, self.log_scroll_offset - 1)
                    elif event.button == 5:  # 向下滚动
                        max_scroll = max(0, len(self.logs) - self.max_visible_logs)
                        self.log_scroll_offset = min(max_scroll, self.log_scroll_offset + 1)

            elif event.type == pygame.MOUSEMOTION and self.state == "game":
                self.handle_mouse_motion(event.pos)

    def handle_menu_click(self, x: int, y: int) -> None:
        """处理菜单点击"""
        # 选择人数
        for i, num in enumerate([2, 3, 4]):
            rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 200 + i * 60, 100, 40)
            if rect.collidepoint(x, y):
                self.selected_num = num

        # 开始游戏
        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 400, 100, 40)
        if start_rect.collidepoint(x, y) and self.selected_num and self.gm:
            self.gm.players = [Player(f"玩家{i+1}", i) for i in range(self.selected_num)]
            self.gm.setup_board()
            self.state = "game"

    def handle_game_click(self, x: int, y: int) -> None:
        """处理游戏点击"""
        if not self.gm or not self.gm.current_player:
            return

        current_player = self.gm.current_player
        
        # 点击卡牌
        clicked_card = self.check_click_card(current_player, x, y)
        if clicked_card:
            self.selected_card = clicked_card
            return

        # 点击目标（对手区域）
        if self.selected_card and getattr(self.selected_card, 'requires_target', False):
            clicked_target = self.check_click_target(current_player, x, y)
            if clicked_target:
                if clicked_target not in self.target_list:
                    self.target_list.append(clicked_target)
                    if clicked_target != current_player:
                        self.enemy_list.append(clicked_target)

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        """处理鼠标移动"""
        if not self.gm or not self.gm.current_player:
            return
            
        x, y = pos
        current_player = self.gm.current_player
        for card in current_player.hand:
            rect = self.get_card_rect_for_card(card, current_player)
            if rect and rect.collidepoint(x, y):
                card.highlight = True
            else:
                card.highlight = False

    def draw_game(self) -> None:
        """绘制游戏界面"""
        self.screen.fill(COLOR_BG)
        
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "game" and self.gm:
            # 绘制所有玩家区域
            for idx, player in enumerate(self.gm.players):
                self.draw_player_zones(player, idx, player == self.gm.current_player)

            # 绘制日志面板
            self.draw_log_panel()

            # 绘制结束回合按钮
            end_turn_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 60, 120, 40)
            pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, end_turn_rect, border_radius=8)
            pygame.draw.rect(self.screen, (200, 200, 230), end_turn_rect, 2, border_radius=8)
            label = self.font_medium.render("结束回合", True, (30, 30, 50))
            label_rect = label.get_rect(center=end_turn_rect.center)
            self.screen.blit(label, label_rect)

            # 绘制消息
            if self.message and self.message_timer > 0:
                # 创建消息背景
                msg_surface = self.font_medium.render(self.message, True, COLOR_TEXT)
                padding = 15
                msg_bg_rect = pygame.Rect(
                    WINDOW_WIDTH // 2 - msg_surface.get_width() // 2 - padding,
                    20,
                    msg_surface.get_width() + padding * 2,
                    msg_surface.get_height() + padding
                )
                pygame.draw.rect(self.screen, (50, 50, 70, 200), msg_bg_rect, border_radius=10)
                pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, msg_bg_rect, 2, border_radius=10)
                self.screen.blit(msg_surface, (msg_bg_rect.x + padding, msg_bg_rect.y + padding//2))
                self.message_timer = max(0, self.message_timer - self.clock.get_time())

        pygame.display.flip()

    def draw_menu(self) -> None:
        """绘制菜单界面"""
        # 标题
        title = self.font_large.render("萝卜昆特牌", True, COLOR_HIGHLIGHT)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("请选择玩家人数", True, COLOR_TEXT)
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 140))
        self.screen.blit(subtitle, subtitle_rect)

        for i, num in enumerate([2, 3, 4]):
            rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 220 + i * 70, 100, 50)
            color = COLOR_HIGHLIGHT if self.selected_num == num else COLOR_ZONE
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, (180, 180, 210), rect, 2, border_radius=10)
            label = self.font_medium.render(f"{num}人", True, COLOR_TEXT)
            label_rect = label.get_rect(center=rect.center)
            self.screen.blit(label, label_rect)

        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 70, 480, 140, 50)
        start_color = COLOR_HIGHLIGHT if self.selected_num else COLOR_ZONE
        pygame.draw.rect(self.screen, start_color, start_rect, border_radius=10)
        pygame.draw.rect(self.screen, (180, 180, 210), start_rect, 2, border_radius=10)
        label = self.font_medium.render("开始游戏", True, COLOR_TEXT)
        label_rect = label.get_rect(center=start_rect.center)
        self.screen.blit(label, label_rect)

    def draw_player_zones(self, player: Player, idx: int, is_current: bool) -> None:
        """绘制玩家区域"""
        base_y = 60 + idx * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        border_color = COLOR_HIGHLIGHT if is_current else COLOR_ZONE
        
        # 绘制玩家区域背景
        zone_rect = pygame.Rect(160, base_y - 35, WINDOW_WIDTH - 320, ZONE_HEIGHT * 3 + 40)
        pygame.draw.rect(self.screen, (50, 50, 65), zone_rect, border_radius=12)
        pygame.draw.rect(self.screen, border_color, zone_rect, 3, border_radius=12)

        # 绘制各个区域
        self.draw_zone("手牌", player.hand, player, "hand", base_y)
        self.draw_zone("战场", player.battlefield_cards, player, "battlefield", base_y + ZONE_HEIGHT + 15)
        self.draw_zone("孤立", player.isolated_cards, player, "isolated", base_y + (ZONE_HEIGHT + 15) * 2)

        # 绘制玩家信息
        info_text = f"{player.name}  分数: {getattr(player, 'score', 0)}  胜局: {getattr(player, 'wins', 0)}"
        name_text = self.font_medium.render(info_text, True, COLOR_HIGHLIGHT if is_current else COLOR_TEXT)
        self.screen.blit(name_text, (25, base_y - 55))

        # 如果是选中的目标，绘制高亮边框
        if player in self.target_list:
            highlight_color = (255, 100, 100) if player in self.enemy_list else (100, 255, 150)
            pygame.draw.rect(self.screen, highlight_color, zone_rect, 4, border_radius=12)

    def draw_zone(self, label: str, cards: List[Card], player: Player, zone_name: str, y: int) -> None:
        """绘制卡牌区域"""
        # 绘制区域标题
        title = self.font_small.render(label, True, COLOR_TEXT)
        self.screen.blit(title, (180, y - 25))

        # 绘制卡牌
        for i, card in enumerate(cards):
            x_pos = 180 + i * (self.card_width + self.card_spacing)
            rect = pygame.Rect(x_pos, y, self.card_width, self.card_height)
            
            # 确定卡牌颜色
            if card == self.selected_card:
                card_color = (180, 120, 255)  # 紫色表示选中
            elif card in self.target_list:
                card_color = (100, 255, 150)  # 绿色表示目标
            else:
                card_color = (70, 70, 100)    # 默认颜色
                
            # 绘制卡牌
            pygame.draw.rect(self.screen, card_color, rect, border_radius=8)
            pygame.draw.rect(self.screen, (150, 150, 180), rect, 2, border_radius=8)
            
            # 悬停效果
            if hasattr(card, "highlight") and card.highlight:
                pygame.draw.rect(self.screen, (255, 255, 150), rect, 3, border_radius=8)

            # 绘制卡牌信息
            # 卡牌名称（限制长度）
            name_text = self.font_tiny.render(card.name[:10], True, COLOR_TEXT)
            self.screen.blit(name_text, (rect.x + 8, rect.y + 8))
            
            # 卡牌点数
            points_text = self.font_small.render(str(card.points), True, (255, 215, 100))
            points_rect = points_text.get_rect(topright=(rect.right - 8, rect.top + 8))
            self.screen.blit(points_text, points_rect)
            
            # 孤立标识
            if getattr(card, 'is_isolated', False):
                iso_text = self.font_tiny.render("[孤]", True, (255, 100, 100))
                self.screen.blit(iso_text, (rect.x + 8, rect.y + 30))
            
            # 技能信息
            if getattr(card, 'skills', None):
                skills_text = self.font_tiny.render("技", True, (100, 200, 255))
                self.screen.blit(skills_text, (rect.x + 8, rect.bottom - 25))

    def draw_log_panel(self) -> None:
        """绘制可滚动的日志面板"""
        # 绘制日志面板背景
        pygame.draw.rect(self.screen, COLOR_LOG_BG, self.log_panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_LOG_BORDER, self.log_panel_rect, 2, border_radius=10)
        
        # 绘制标题
        title = self.font_small.render("操作记录", True, COLOR_HIGHLIGHT)
        self.screen.blit(title, (self.log_panel_rect.x + 15, self.log_panel_rect.y + 10))
        
        # 绘制日志内容
        if self.logs:
            # 计算可见日志范围
            start_idx = self.log_scroll_offset
            end_idx = min(start_idx + self.max_visible_logs, len(self.logs))
            
            # 绘制可见的日志
            for i in range(start_idx, end_idx):
                log_text = self.logs[i]
                # 限制日志文本长度
                if len(log_text) > 80:
                    log_text = log_text[:77] + "..."
                
                text_surface = self.font_tiny.render(log_text, True, COLOR_TEXT)
                y_pos = self.log_panel_rect.y + 40 + (i - start_idx) * 20
                self.screen.blit(text_surface, (self.log_panel_rect.x + 15, y_pos))
        
        # 绘制滚动条
        if len(self.logs) > self.max_visible_logs:
            # 计算滚动条位置和大小
            scrollbar_height = max(30, self.log_panel_rect.height * (self.max_visible_logs / len(self.logs)))
            scrollbar_y_offset = (self.log_panel_rect.height - 40) * (self.log_scroll_offset / max(1, len(self.logs) - self.max_visible_logs))
            
            # 更新滚动条矩形位置
            self.scrollbar_rect = pygame.Rect(
                self.log_panel_rect.right - 25,
                self.log_panel_rect.top + 20 + scrollbar_y_offset,
                20,
                scrollbar_height
            )
            
            # 绘制滚动条
            pygame.draw.rect(self.screen, COLOR_SCROLLBAR, self.scrollbar_rect, border_radius=3)
            pygame.draw.rect(self.screen, (200, 200, 230), self.scrollbar_rect, 1, border_radius=3)

    def check_click_card(self, player: Player, x: int, y: int, zone: str = "hand") -> Optional[Card]:
        """检查是否点击到卡牌"""
        cards = []
        base_y = 60 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        y_offset = 0
        
        if zone == "hand":
            cards = player.hand
            y_offset = 0
        elif zone == "battlefield":
            cards = player.battlefield_cards
            y_offset = ZONE_HEIGHT + 15
        elif zone == "isolated":
            cards = player.isolated_cards
            y_offset = (ZONE_HEIGHT + 15) * 2
        else:
            return None

        for i, card in enumerate(cards):
            rect = pygame.Rect(
                180 + i * (self.card_width + self.card_spacing),
                base_y + y_offset,
                self.card_width,
                self.card_height
            )
            if rect.collidepoint(x, y):
                return card
        return None

    def check_click_target(self, current_player: Player, x: int, y: int) -> Optional[Player]:
        """检查是否点击到目标玩家区域"""
        if not self.gm:
            return None
            
        for player in self.gm.players:
            base_y = 60 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
            rect = pygame.Rect(160, base_y - 35, WINDOW_WIDTH - 320, ZONE_HEIGHT * 3 + 40)
            if rect.collidepoint(x, y):
                return player
        return None

    def get_card_rect_for_card(self, card: Card, player: Player, zone: str = "hand") -> Optional[pygame.Rect]:
        """获取卡牌的矩形区域"""
        base_y = 60 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        y_offset = 0
        
        if zone == "hand":
            cards = player.hand
            y_offset = 0
        elif zone == "battlefield":
            cards = player.battlefield_cards
            y_offset = ZONE_HEIGHT + 15
        elif zone == "isolated":
            cards = player.isolated_cards
            y_offset = (ZONE_HEIGHT + 15) * 2
        else:
            return None

        for i, c in enumerate(cards):
            if c == card:
                return pygame.Rect(
                    180 + i * (self.card_width + self.card_spacing),
                    base_y + y_offset,
                    self.card_width,
                    self.card_height
                )
        return None