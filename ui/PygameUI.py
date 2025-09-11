import pygame
import sys
from typing import Optional, Dict, Any, List, cast
from game.player import Player
from game.card import Card
from game.game_manager import GameManager
from ui.constants import *

class PygameUI:
    # 类级默认值用于静态检查（实例会在 __init__ 中覆盖）
    hover_card: Optional[Card] = None
    hover_start_ms: int = 0
    hover_delay_ms: int = 600
    mouse_pos: tuple[int, int] = (0, 0)
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("萝卜昆特牌")

        # 选择更稳妥的中文字体（带回退列表），确保宽度测量与渲染一致
        font_candidates = [
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "SimHei",
            "msyh",
            "Arial Unicode MS",
        ]
        self.font = pygame.font.SysFont(font_candidates, 24)
        self.small_font = pygame.font.SysFont(font_candidates, 16)
        self.clock = pygame.time.Clock()

        # 游戏状态
        self.running = True
        self.state = "menu"
        self.selected_num = None
        self.selected_card = None
        self.target_list = []      # 存储目标卡牌
        self.enemy_list = []       # 存储目标玩家
        self.message = ""
        self.message_timer = 0

        # 底部日志
        self.logs = []
        self.max_logs = 6  # 底部显示的日志行数

        # Manager 绑定
        self.gm = None
        # 游戏结束信息
        self.game_over_winners = []

        # 卡片绘制参数
        self.card_width = 60
        self.card_height = 90
        self.card_spacing = 10   # 原为5，增大以避免遮挡
        self.card_left = 150

        # 悬停提示（技能说明）
        self.hover_card = None            # 当前鼠标悬停的卡牌
        self.hover_start_ms = 0           # 开始悬停的时间戳（ms）
        self.hover_delay_ms = 600         # 悬停多少毫秒后显示提示
        self.mouse_pos = (0, 0)           # 记录鼠标位置用于提示框定位
    
    def _build_card_rects(self, cards: List[Card], y: int) -> List[pygame.Rect]:
        """根据卡名实际宽度为一行卡牌构建矩形列表，保证卡名完整显示。"""
        rects: List[pygame.Rect] = []
        x = self.card_left
        for c in cards:
            # 卡面主标题（含点数、孤立标识）决定卡宽
            text = f"{c.name}({c.points})"
            # 不再在卡牌前加“[孤]”标记
            # 使用实际渲染后的表面宽度，避免字体度量偏差导致截断
            text_surface = self.font.render(text, True, COLOR_TEXT)
            text_w = text_surface.get_width()
            width = max(self.card_width, text_w + 16)  # 左右预留更充足的 padding
            rects.append(pygame.Rect(x, y, width, self.card_height))
            x += width + self.card_spacing
        return rects

    def compute_live_score(self, player: Player) -> int:
        """实时计算玩家当前分数（战场+孤立区点数和）。"""
        return sum(c.points for c in player.battlefield_cards + player.isolated_cards)

    def set_manager(self, gm: GameManager) -> None:
        """设置游戏管理器"""
        self.gm = gm

    def show_message(self, text: str, duration: int = 2000) -> None:
        """显示消息"""
        self.message = text
        self.message_timer = duration

    def add_log(self, text: str) -> None:
        """追加一条日志到底部日志框。"""
        if not isinstance(text, str):
            text = str(text)
        self.logs.append(text)
        if len(self.logs) > 200:
            # 控制日志总量
            self.logs = self.logs[-200:]

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

    def select_cards_from_hand(self, player: Player, count: int, prompt: str = "请选择卡牌并点击确认") -> List[Card]:
        """阻塞等待玩家从手牌中选择 count 张卡牌，点击“确认”按钮后返回。
        - 允许重复点击同一张手牌以取消选择。
        - 只有当选择数量达到 count 时，确认按钮才可用。
        返回选择的卡牌列表；若中途退出或异常，则返回当前已选（可能不足 count）。
        """
        chosen: List[Card] = []
        # 保存现场并清空当前选择，避免与主循环状态冲突
        prev_selected = self.selected_card
        prev_targets = list(self.target_list)
        prev_enemies = list(self.enemy_list)
        self.selected_card = None
        self.target_list = []
        self.enemy_list = []

        # 放在更靠左的位置，避免与“出牌/结束回合”按钮重叠
        confirm_rect = pygame.Rect(WINDOW_WIDTH - 450, WINDOW_HEIGHT - 60, 120, 40)
        while self.running:
            # 提示文案
            remain = max(0, count - len(chosen))
            tip = f"{prompt}（还需选择 {remain} 张）"
            self.show_message(tip)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # 选择/取消选择手牌
                    card = self.check_click_card(player, x, y, "hand")
                    if card:
                        if card in chosen:
                            chosen.remove(card)
                        else:
                            if len(chosen) < count:
                                chosen.append(card)
                        continue

                    # 确认按钮：仅在数量达标时可用
                    if confirm_rect.collidepoint(x, y) and len(chosen) == count:
                        # 恢复现场
                        self.selected_card = prev_selected
                        self.target_list = prev_targets
                        self.enemy_list = prev_enemies
                        self.show_message("")
                        return chosen

            # 绘制界面（按钮与已选高亮）
            self.draw_game()
            # 绘制确认按钮（覆盖在底部日志上层）
            pygame.draw.rect(self.screen, COLOR_HIGHLIGHT if len(chosen) == count else COLOR_ZONE, confirm_rect)
            label = self.font.render("确认", True, COLOR_TEXT)
            self.screen.blit(label, (confirm_rect.x + 35, confirm_rect.y + 5))

            # 在当前玩家手牌中高亮已选卡牌
            # 这里不直接改 card.highlight，避免干扰 hover；只在按钮旁边列出已选
            if chosen:
                names = ", ".join(c.name for c in chosen)
                info = self.small_font.render(f"已选：{names}", True, COLOR_TEXT)
                self.screen.blit(info, (confirm_rect.x - 260, confirm_rect.y + 10))

            pygame.display.flip()
            self.clock.tick(30)

        # 退出时恢复现场
        self.selected_card = prev_selected
        self.target_list = prev_targets
        self.enemy_list = prev_enemies
        return chosen

    def wait_for_player_action(self, player: Player) -> Dict[str, Any]:
        """等待玩家操作"""
        waiting = True
        result = {"type": END_TURN}  # 默认为结束回合
        
        while waiting and self.running:
            # 检查是否有卡牌被选中
            if self.selected_card:
                ui_message = f"已选择卡牌: {self.selected_card.name}"
                # 如果需要选择敌方玩家（拼点等）
                if self.selected_card.requires_enemy:
                    if not self.enemy_list:
                        ui_message += "\n【请点击一位敌方玩家作为目标】"
                    else:
                        enemy_names = [p.name for p in self.enemy_list]
                        ui_message += f"\n已选择敌方玩家：{', '.join(enemy_names)}"
                
                # 如果需要选择目标卡牌（援助、精准打击等）
                elif self.selected_card.requires_target:
                    zone_type = self.selected_card.target_type
                    target_side = self.selected_card.target_side
                    
                    if not self.target_list:
                        zone_text = "战场" if zone_type == "battlefield" else "手牌" if zone_type == "hand" else "孤立区"
                        side_text = "自己的" if target_side == "self" else "其他玩家的" if target_side == "other" else "任意玩家的"
                        ui_message += f"\n【请选择{side_text}{zone_text}卡牌作为目标】"
                    else:
                        target_cards = [f"{card.name}" for card in self.target_list]
                        ui_message += f"\n已选择目标卡牌：{', '.join(target_cards)}"
                ui_message += "\n点击[出牌]按钮确认出牌"
                self.show_message(ui_message)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEMOTION:
                    # 更新悬停状态以支持提示
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos

                    # 1) 当前玩家手牌点击：选择/切换/取消
                    clicked_hand_card = self.check_click_card(player, x, y, "hand")
                    if clicked_hand_card:
                        if not self.selected_card:
                            # 选择一张手牌
                            self.selected_card = clicked_hand_card
                            self.target_list = []
                            self.enemy_list = []
                            continue
                        if clicked_hand_card == self.selected_card:
                            # 再次点击同一张手牌 -> 取消选择
                            self.selected_card = None
                            self.target_list = []
                            self.enemy_list = []
                            continue
                        else:
                            # 切换手牌选择
                            self.selected_card = clicked_hand_card
                            self.target_list = []
                            self.enemy_list = []
                            continue

                    # 2) 已选择手牌时，处理目标/敌人选择
                    if self.selected_card:
                        clicked_target = self.check_click_target(player, x, y)
                        if clicked_target:
                            # 敌方玩家目标（仅玩家，例：拼点9）
                            if self.selected_card.requires_enemy and not self.selected_card.requires_target:
                                if clicked_target == player:
                                    # 点击自己 -> 取消选择
                                    self.selected_card = None
                                    self.target_list = []
                                    self.enemy_list = []
                                else:
                                    # 选择/切换敌人
                                    if clicked_target in self.enemy_list:
                                        self.enemy_list.remove(clicked_target)
                                    else:
                                        self.enemy_list = [clicked_target]
                                continue

                            # 卡牌目标（援助3/精准打击7等）
                            if self.selected_card.requires_target:
                                # 阵营限制：self/other/any
                                side = self.selected_card.target_side
                                if side == "other" and clicked_target == player:
                                    # 只允许选择其他玩家
                                    continue
                                if side == "self" and clicked_target != player:
                                    # 只允许选择自己
                                    continue

                                clicked_target_card = self.check_click_card(
                                    clicked_target,
                                    x,
                                    y,
                                    self.selected_card.target_type,
                                )
                                if clicked_target_card:
                                    if clicked_target_card in self.target_list:
                                        self.target_list.remove(clicked_target_card)
                                    else:
                                        self.target_list = [clicked_target_card]
                                continue

                    # 3) 出牌按钮（现在 target/enemy 已更新）
                    play_card_rect = pygame.Rect(WINDOW_WIDTH - 300, WINDOW_HEIGHT - 60, 120, 40)
                    if play_card_rect.collidepoint(x, y) and self.selected_card:
                        if (not self.selected_card.requires_enemy or self.enemy_list) and (
                            not self.selected_card.requires_target or self.target_list
                        ):
                            result = {
                                "type": PLAY_CARD,
                                "card": self.selected_card,
                                "targets": self.target_list,
                                "enemies": self.enemy_list,
                            }
                            self.selected_card = None
                            self.target_list = []
                            self.enemy_list = []
                            return result
                        else:
                            need = []
                            if self.selected_card.requires_enemy and not self.enemy_list:
                                need.append("敌方玩家")
                            if self.selected_card.requires_target and not self.target_list:
                                need.append("目标卡牌")
                            if need:
                                self.show_message(f"请先选择{' 和 '.join(need)}")
                            continue

                    # 4) 结束回合按钮
                    end_turn_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 60, 120, 40)
                    if end_turn_rect.collidepoint(x, y):
                        if self.selected_card:
                            # 有选中的手牌 -> 取消选择
                            self.selected_card = None
                            self.target_list = []
                            self.enemy_list = []
                            continue
                        result = {"type": END_TURN}
                        waiting = False
                        break

            self.draw_game()
            self.clock.tick(30)

        # 重置选择状态
        self.selected_card = None
        self.target_list = []
        self.enemy_list = []
        return result

    def player_end_turn(self, player: Player) -> bool:
        """检查玩家是否结束回合"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEMOTION:
                # 更新悬停提示
                self.handle_mouse_motion(event.pos)
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
                elif self.state == "game_over":
                    self.handle_game_over_click(x, y)
            elif event.type == pygame.MOUSEMOTION and self.state == "game":
                self.handle_mouse_motion(event.pos)

    def _get_card_under_mouse(self, x: int, y: int) -> Optional[Card]:
        """返回鼠标下的卡牌（任意玩家任意区域），若无则返回 None。"""
        if not self.gm:
            return None
        for player in self.gm.players:
            # 依次检查手牌/战场/孤立
            for zone in ("hand", "battlefield", "isolated"):
                card = self.check_click_card(player, x, y, zone)
                if card:
                    return card
        return None

    def _get_card_rect(self, card: Card) -> Optional[pygame.Rect]:
        """获取某张卡牌当前屏幕上的矩形（查找所有玩家与区域）。"""
        if not self.gm:
            return None
        for player in self.gm.players:
            for zone in ("hand", "battlefield", "isolated"):
                rect = self.get_card_rect_for_card(card, player, zone)
                if rect is not None:
                    return rect
        return None

    def _collect_skill_tooltip_lines(self, card: Card) -> list[str]:
        """从卡牌生成提示文案：基础点数 + 每个技能的第一行说明。"""
        lines: list[str] = []
        # 基础点数
        base = getattr(card, "base_points", card.points)
        lines.append(f"基础点数：{base}")
        if not getattr(card, "skills", None):
            return lines
        for s in card.skills:
            doc = (s.__class__.__doc__ or "").strip()
            # 仅取第一行，以免过长
            first_line = doc.splitlines()[0] if doc else ""
            if first_line:
                lines.append(f"【{getattr(s, 'name', s.__class__.__name__)}】{first_line}")
            else:
                lines.append(f"【{getattr(s, 'name', s.__class__.__name__)}】无技能说明")
        return lines

    def _draw_tooltip(self) -> None:
        """在需要时绘制悬停提示框。"""
        if not self.hover_card:
            return
        # 是否达到延迟
        now = pygame.time.get_ticks()
        if self.hover_start_ms == 0 or now - self.hover_start_ms < self.hover_delay_ms:
            return

        lines = self._collect_skill_tooltip_lines(self.hover_card)
        if not lines:
            return

        # 组装文本，自动换行
        wrapped: list[str] = []
        max_width = 320
        for line in lines:
            wrapped.extend(self._wrap_text(line, self.small_font, max_width - 16))
        if not wrapped:
            return

        # 计算提示框尺寸
        line_h = 18
        padding = 8
        text_w = 0
        for seg in wrapped:
            w, _ = self.small_font.size(seg)
            text_w = max(text_w, w)
        box_w = min(max_width, text_w + padding * 2)
        box_h = padding * 2 + line_h * len(wrapped)

        # 确定位置（靠近鼠标，避免越界）
        mx, my = self.mouse_pos
        x = mx + 14
        y = my + 14
        if x + box_w > WINDOW_WIDTH:
            x = WINDOW_WIDTH - box_w - 10
        if y + box_h > WINDOW_HEIGHT:
            y = WINDOW_HEIGHT - box_h - 10

        # 绘制背景与边框
        bg_color = (30, 30, 30)
        border_color = (200, 200, 200)
        pygame.draw.rect(self.screen, bg_color, pygame.Rect(x, y, box_w, box_h))
        pygame.draw.rect(self.screen, border_color, pygame.Rect(x, y, box_w, box_h), 1)

        # 绘制文本
        ty = y + padding
        for seg in wrapped:
            surf = self.small_font.render(seg, True, COLOR_TEXT)
            self.screen.blit(surf, (x + padding, ty))
            ty += line_h

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

        # 先检查是否点击了任何玩家的区域
        clicked_target = self.check_click_target(current_player, x, y)
        
        if not clicked_target:
            return
            
        # 检查是否点击了当前玩家的手牌
        if clicked_target == current_player:
            hand_card = self.check_click_card(clicked_target, x, y, "hand")
            if hand_card:
                if not self.selected_card:  # 选择手牌
                    self.selected_card = hand_card
                    self.target_list = []
                    self.enemy_list = []
                    print(f"选择手牌: {hand_card.name}")
                elif hand_card == self.selected_card:  # 取消选择
                    self.selected_card = None
                    self.target_list = []
                    self.enemy_list = []
                    print("取消选择手牌")
                return

        # 处理已经选择了一张卡牌的情况
        if not self.selected_card:
            return

        print(f"点击了玩家 {clicked_target.name} 的区域")

        # 处理需要敌方目标的情况（拼点）
        if self.selected_card.requires_enemy and not self.selected_card.requires_target:
            if clicked_target == current_player:
                self.selected_card = None
                self.enemy_list = []
                print("取消选择")
                return
                
            if clicked_target in self.enemy_list:
                self.enemy_list.remove(clicked_target)
                print(f"取消选择敌方目标: {clicked_target.name}")
            else:
                self.enemy_list = [clicked_target]
                print(f"选择敌方目标: {clicked_target.name}")
            return

        # 处理需要卡牌目标的情况（援助、精准打击等）
        if self.selected_card.requires_target:
            # 如果点击了自己的区域，且不是选择自己的卡牌技能
            if clicked_target == current_player and self.selected_card.target_side == "other":
                print(f"错误：{self.selected_card.name}只能选择其他玩家的卡牌")
                return
                
            # 如果点击了其他玩家的区域，且只能选择自己的卡牌
            if clicked_target != current_player and self.selected_card.target_side == "self":
                print(f"错误：{self.selected_card.name}只能选择自己的卡牌")
                return

            # 检查点击的卡牌
            clicked_card = self.check_click_card(
                clicked_target,
                x, y,
                self.selected_card.target_type
            )
                    
            if clicked_card:
                if clicked_card in self.target_list:
                    self.target_list.remove(clicked_card)
                    print(f"取消选择目标卡牌: {clicked_card.name}")
                else:
                    self.target_list = [clicked_card]
                    print(f"选择目标卡牌: {clicked_card.name} (在{clicked_target.name}的{self.selected_card.target_type}区域)")
            return

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        """处理鼠标移动"""
        if not self.gm or not self.gm.current_player:
            return
            
        x, y = pos
        # 更新鼠标位置与悬停状态
        self.mouse_pos = (x, y)
        hovered_card = self._get_card_under_mouse(x, y)
        if hovered_card is not self.hover_card:
            self.hover_card = hovered_card
            self.hover_start_ms = pygame.time.get_ticks() if hovered_card else 0
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

            # 先绘制底部日志框，按钮稍后再画在其上层
            self.draw_log_panel()

            # 绘制出牌按钮（在日志之上）
            play_card_rect = pygame.Rect(WINDOW_WIDTH - 300, WINDOW_HEIGHT - 60, 120, 40)
            play_color = COLOR_HIGHLIGHT if self.selected_card else COLOR_ZONE
            pygame.draw.rect(self.screen, play_color, play_card_rect)
            label = self.font.render("出牌", True, COLOR_TEXT)
            self.screen.blit(label, (play_card_rect.x + 35, play_card_rect.y + 5))

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

            # 绘制悬停提示（技能说明）
            self._draw_tooltip()
        elif self.state == "game_over":
            self.draw_game_over()

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

    def draw_game_over(self) -> None:
        """绘制大局结束界面：比分、胜者、操作按钮"""
        # 标题
        title = self.font.render("大局结束", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 80))

        # 胜者
        winners_text = ", ".join(self.game_over_winners) if self.game_over_winners else "无"
        winners_surface = self.font.render(f"胜利者: {winners_text}", True, COLOR_TEXT)
        self.screen.blit(winners_surface, (WINDOW_WIDTH // 2 - winners_surface.get_width() // 2, 140))

        # 大比分（小局胜场）
        if self.gm:
            y = 200
            score_title = self.font.render("比分（小局胜场）:", True, COLOR_TEXT)
            self.screen.blit(score_title, (WINDOW_WIDTH // 2 - score_title.get_width() // 2, y))
            y += 40
            for name, wins in self.gm.small_rounds_won.items():
                line = self.font.render(f"{name}: {wins}", True, COLOR_TEXT)
                self.screen.blit(line, (WINDOW_WIDTH // 2 - line.get_width() // 2, y))
                y += 30

        # 操作按钮
        menu_rect = pygame.Rect(WINDOW_WIDTH // 2 - 170, WINDOW_HEIGHT - 200, 150, 50)
        exit_rect = pygame.Rect(WINDOW_WIDTH // 2 + 20, WINDOW_HEIGHT - 200, 150, 50)
        pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, menu_rect)
        pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, exit_rect)
        menu_label = self.font.render("返回主页", True, COLOR_TEXT)
        exit_label = self.font.render("退出游戏", True, COLOR_TEXT)
        self.screen.blit(menu_label, (menu_rect.x + (150 - menu_label.get_width()) // 2, menu_rect.y + 10))
        self.screen.blit(exit_label, (exit_rect.x + (150 - exit_label.get_width()) // 2, exit_rect.y + 10))

    def handle_game_over_click(self, x: int, y: int) -> None:
        """处理游戏结束界面的点击"""
        menu_rect = pygame.Rect(WINDOW_WIDTH // 2 - 170, WINDOW_HEIGHT - 200, 150, 50)
        exit_rect = pygame.Rect(WINDOW_WIDTH // 2 + 20, WINDOW_HEIGHT - 200, 150, 50)
        if menu_rect.collidepoint(x, y):
            self.reset_to_menu()
        elif exit_rect.collidepoint(x, y):
            self.running = False

    def show_game_over(self, winners: List[str]) -> None:
        """进入大局结束界面并记录胜者"""
        self.game_over_winners = winners
        self.state = "game_over"

    def reset_to_menu(self) -> None:
        """回到主页菜单，重置状态"""
        # 清理 UI 状态
        self.selected_num = None
        self.selected_card = None
        self.target_list.clear()
        self.enemy_list.clear()
        self.logs.clear()
        self.message = ""
        self.message_timer = 0
        # 重置游戏管理器
        if self.gm:
            self.gm.reset_for_new_game()
        # 切换到菜单
        self.state = "menu"

    def draw_player_zones(self, player: Player, idx: int, is_current: bool) -> None:
        """绘制玩家区域"""
        base_y = 50 + idx * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        border_color = COLOR_CURRENT if is_current else COLOR_ZONE
        # 如果当前有选中卡牌且需要选择目标，显示玩家区域的可选状态
        if self.selected_card and self.gm and self.gm.current_player:
            current_player = self.gm.current_player
            if self.selected_card.requires_enemy and player != current_player:
                # 对于需要选择敌方的卡牌，其他玩家区域显示为红色
                border_color = (200, 100, 100)  # 红色表示可以选择为目标
            # 不再高亮显示需要卡牌目标的玩家区域

        # 绘制玩家区域边框
        pygame.draw.rect(self.screen, border_color,
                        (140, base_y - 30, WINDOW_WIDTH - 280, ZONE_HEIGHT * 3 + 30), 2)

        # 绘制各个区域
        self.draw_zone("手牌", player.hand, player, "hand", base_y)
        self.draw_zone("战场", player.battlefield_cards, player, "battlefield", base_y + ZONE_HEIGHT + 10)
        self.draw_zone("孤立", player.isolated_cards, player, "isolated", base_y + (ZONE_HEIGHT + 10) * 2)

        # 绘制玩家信息：分数使用实时分（战场+孤立区）
        live_score = self.compute_live_score(player)
        info_text = f"{player.name}  分数: {live_score}  胜局: {player.wins}"
        name_text = self.font.render(info_text, True, COLOR_TEXT)
        self.screen.blit(name_text, (20, base_y - 50))

        # 如果是选中的目标，绘制高亮边框
        if player in self.target_list:
            highlight_color = (255, 0, 0) if player in self.enemy_list else (0, 255, 0)
            pygame.draw.rect(self.screen, highlight_color,
                           (140, base_y - 30, WINDOW_WIDTH - 280, ZONE_HEIGHT * 3 + 30), 4)

    def draw_log_panel(self) -> None:
        """在底部绘制一个日志框，显示最近的操作。"""
        panel_height = 140
        panel_rect = pygame.Rect(0, WINDOW_HEIGHT - panel_height, WINDOW_WIDTH, panel_height)
        pygame.draw.rect(self.screen, (20, 20, 20), panel_rect)
        pygame.draw.rect(self.screen, (80, 80, 80), panel_rect, 2)

        # 标题
        title = self.font.render("操作记录", True, COLOR_TEXT)
        self.screen.blit(title, (10, WINDOW_HEIGHT - panel_height + 10))

        # 取最后 max_logs 条
        lines = self.logs[-self.max_logs:]
        # 从底部向上画
        for i, line in enumerate(reversed(lines)):
            text_surface = self.font.render(line, True, COLOR_TEXT)
            y = WINDOW_HEIGHT - 10 - (i + 1) * (text_surface.get_height() + 2)
            self.screen.blit(text_surface, (10, y))

    def draw_zone(self, label: str, cards: List[Card], player: Player, zone_name: str, y: int) -> None:
        """绘制卡牌区域"""
        title = self.font.render(label, True, COLOR_TEXT)
        self.screen.blit(title, (150, y - 20))
        rects = self._build_card_rects(cards, y)
        for card, rect in zip(cards, rects):
            # 根据不同情况设置卡牌颜色
            if card == self.selected_card:
                color = COLOR_HIGHLIGHT  # 选中的卡牌
            elif card in self.target_list:
                color = (100, 200, 100)  # 被选为目标的卡牌显示为绿色
            else:
                color = (100, 100, 100)  # 普通卡牌

            pygame.draw.rect(self.screen, color, rect)

            # 如果鼠标悬停在卡牌上
            if hasattr(card, "highlight") and card.highlight:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 3)

            # 绘制卡牌基本信息（卡名必须完整显示，卡片宽度已动态调整）
            card_info = f"{card.name}({card.points})"
            # 不再在卡牌前加“[孤]”标记
            card_text = self.font.render(card_info, True, COLOR_TEXT)
            self.screen.blit(card_text, (rect.x + 5, rect.y + 5))

            # 绘制技能名称：自动换行显示完整技能名，尽量在可用高度内展示
            if card.skills:
                line_y_start = rect.y + 35
                line_h = 16
                max_lines = max(0, (self.card_height - (line_y_start - rect.y) - 6) // line_h)
                avail_w = rect.width - 10
                names = [getattr(s, 'name', str(s)) for s in card.skills]
                wrapped_lines: List[str] = []
                for name in names:
                    if max_lines and len(wrapped_lines) >= max_lines:
                        break
                    wrapped = self._wrap_text(name, self.small_font, avail_w)
                    for seg in wrapped:
                        if max_lines and len(wrapped_lines) >= max_lines:
                            break
                        wrapped_lines.append(seg)
                # 绘制最终行
                for j, line in enumerate(wrapped_lines):
                    skill_text = self.small_font.render(line, True, COLOR_TEXT)
                    self.screen.blit(skill_text, (rect.x + 5, line_y_start + j * line_h))

    def check_click_card(self, player: Player, x: int, y: int, zone: str = "hand") -> Optional[Card]:
        """检查是否点击到卡牌
        
        :param zone: 要检查的区域，可以是 "hand"/"battlefield"/"isolated"
        """
        cards: List[Card] = []
        base_y = 50 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN)

        if zone == "hand":
            cards = player.hand
            y_offset = 0
        elif zone == "battlefield":
            cards = player.battlefield_cards
            y_offset = ZONE_HEIGHT + 10
        elif zone == "isolated":
            cards = player.isolated_cards
            y_offset = (ZONE_HEIGHT + 10) * 2
        else:
            return None

        rects = self._build_card_rects(cards, base_y + y_offset)
        for card, rect in zip(cards, rects):
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

    def get_card_rect_for_card(self, card: Card, player: Player, zone: str = "hand") -> Optional[pygame.Rect]:
        """获取卡牌的矩形区域
        
        :param zone: 要检查的区域，可以是 "hand"/"battlefield"/"isolated"
        """
        base_y = 50 + player.index * (ZONE_HEIGHT * 3 + ZONE_MARGIN)
        
        # 确定要搜索的卡牌列表和纵向偏移
        if zone == "hand":
            cards = player.hand
            y_offset = 0
        elif zone == "battlefield":
            cards = player.battlefield_cards
            y_offset = ZONE_HEIGHT + 10
        elif zone == "isolated":
            cards = player.isolated_cards
            y_offset = (ZONE_HEIGHT + 10) * 2
        else:
            return None

        # 在指定区域中查找卡牌
        rects = self._build_card_rects(cards, base_y + y_offset)
        for c, r in zip(cards, rects):
            if c == card:
                return r
        return None

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """将字符串按像素宽度换行，适配中英文混排。
        规则：逐字累积，超过 max_width 则换行；不添加省略号。
        """
        if not text:
            return [""]
        lines: List[str] = []
        current = ""
        for ch in text:
            test = current + ch
            if font.size(test)[0] <= max_width or not current:
                current = test
            else:
                lines.append(current)
                current = ch
        if current:
            lines.append(current)
        return lines
