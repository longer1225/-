import pygame
import sys
from typing import Optional, Dict, Any, List
from game.player import Player
from game.card import Card
from game.game_manager import GameManager

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

# 事件常量
END_TURN = 1
PLAY_CARD = 2
SELECT_TARGET = 3

class PygameUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("萝卜昆特牌")

        self.font = pygame.font.SysFont("simhei", 24)
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

        # Manager 绑定
        self.gm: Optional[GameManager] = None

    def set_manager(self, gm: GameManager) -> None:
        """设置游戏管理器"""
        self.gm = gm

    def show_message(self, text: str, duration: int = 2000) -> None:
        """显示消息"""
        self.message = text
        self.message_timer = duration

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

            # 绘制结束回合按钮
            end_turn_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 60, 120, 40)
            pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, end_turn_rect)
            label = self.font.render("结束回合", True, COLOR_TEXT)
            self.screen.blit(label, (end_turn_rect.x + 10, end_turn_rect.y + 5))

            # 绘制消息
            if self.message and self.message_timer > 0:
                msg_surface = self.font.render(self.message, True, COLOR_TEXT)
                self.screen.blit(msg_surface, (WINDOW_WIDTH // 2 - msg_surface.get_width() // 2, 10))
                self.message_timer = max(0, self.message_timer - self.clock.get_time())

        pygame.display.flip()

    def draw_menu(self) -> None:
        """绘制菜单界面"""
        title = self.font.render("请选择玩家人数", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - 100, 100))

        for i, num in enumerate([2, 3, 4]):
            rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 200 + i * 60, 100, 40)
            color = COLOR_HIGHLIGHT if self.selected_num == num else COLOR_ZONE
            pygame.draw.rect(self.screen, color, rect)
            label = self.font.render(f"{num}人", True, COLOR_TEXT)
            self.screen.blit(label, (rect.x + 20, rect.y + 5))

        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, 400, 100, 40)
        pygame.draw.rect(self.screen, COLOR_HIGHLIGHT if self.selected_num else COLOR_ZONE, start_rect)
        label = self.font.render("开始游戏", True, COLOR_TEXT)
        self.screen.blit(label, (start_rect.x + 5, start_rect.y + 5))

    def draw_player_zones(self, player: Player, idx: int, is_current: bool) -> None:
        """绘制玩家区域"""
        base_y = 50 + idx * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        border_color = COLOR_CURRENT if is_current else COLOR_ZONE
        pygame.draw.rect(self.screen, border_color,
                        (140, base_y - 30, WINDOW_WIDTH - 280, ZONE_HEIGHT * 3 + 30), 2)

        # 绘制各个区域
        self.draw_zone("手牌", player.hand, player, "hand", base_y)
        self.draw_zone("战场", player.battlefield_cards, player, "battlefield", base_y + ZONE_HEIGHT + 10)
        self.draw_zone("孤立", player.isolated_cards, player, "isolated", base_y + (ZONE_HEIGHT + 10) * 2)

        # 绘制玩家信息
        info_text = f"{player.name}  分数: {player.score}  胜局: {player.wins}"
        name_text = self.font.render(info_text, True, COLOR_TEXT)
        self.screen.blit(name_text, (20, base_y - 50))

        # 如果是选中的目标，绘制高亮边框
        if player in self.target_list:
            highlight_color = (255, 0, 0) if player in self.enemy_list else (0, 255, 0)
            pygame.draw.rect(self.screen, highlight_color,
                           (140, base_y - 30, WINDOW_WIDTH - 280, ZONE_HEIGHT * 3 + 30), 4)

    def draw_zone(self, label: str, cards: List[Card], player: Player, zone_name: str, y: int) -> None:
        """绘制卡牌区域"""
        title = self.font.render(label, True, COLOR_TEXT)
        self.screen.blit(title, (150, y - 20))

        for i, card in enumerate(cards):
            rect = pygame.Rect(150 + i * (60 + 5), y, 60, 90)
            color = COLOR_HIGHLIGHT if card == self.selected_card else (100, 100, 100)
            pygame.draw.rect(self.screen, color, rect)
            
            if hasattr(card, "highlight") and card.highlight:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 3)

            # 绘制卡牌信息
            card_text = self.font.render(str(card), True, COLOR_TEXT)
            self.screen.blit(card_text, (rect.x + 5, rect.y + 5))

    def check_click_card(self, player: Player, x: int, y: int) -> Optional[Card]:
        """检查是否点击到卡牌"""
        for i, card in enumerate(player.hand):
            rect = pygame.Rect(150 + i * (60 + 5), 50 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN), 60, 90)
            if rect.collidepoint(x, y):
                return card
        return None

    def check_click_target(self, current_player: Player, x: int, y: int) -> Optional[Player]:
        """检查是否点击到目标玩家区域"""
        if not self.gm:
            return None
            
        for player in self.gm.players:
            rect = pygame.Rect(140, 50 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN) - 30,
                             WINDOW_WIDTH - 280, ZONE_HEIGHT * 3 + 30)
            if rect.collidepoint(x, y):
                return player
        return None

    def get_card_rect_for_card(self, card: Card, player: Player) -> Optional[pygame.Rect]:
        """获取卡牌的矩形区域"""
        for i, c in enumerate(player.hand):
            if c == card:
                return pygame.Rect(150 + i * (60 + 5), 50 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN), 60, 90)
        return None
