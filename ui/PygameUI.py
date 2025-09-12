import pygame
import os
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
        # 背景水印字号放大以增强区域辨识度
        self.wm_font = pygame.font.SysFont(font_candidates, 40)
        # 主页大标题字体
        self.title_font = pygame.font.SysFont(font_candidates, 72)
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
        # 固定卡宽（每局开始时计算一次，之后不再改变）
        self.fixed_card_width = None

        # 卡牌背景图
        self.card_bg = None
        self.card_bg_scaled = None
        try:
            img_path = os.path.join(os.path.dirname(__file__), "images", "card.jpg")
            if os.path.exists(img_path):
                self.card_bg = pygame.image.load(img_path).convert_alpha()
        except Exception:
            self.card_bg = None

        # 全局背景图
        self.bg_image = None
        self.bg_scaled = None
        try:
            bg_path = os.path.join(os.path.dirname(__file__), "images", "background.jpg")
            if os.path.exists(bg_path):
                self.bg_image = pygame.image.load(bg_path).convert()
        except Exception:
            self.bg_image = None

        # 通用按钮背景图
        self.btn_image = None
        try:
            btn_path = os.path.join(os.path.dirname(__file__), "images", "botton.jpg")
            if os.path.exists(btn_path):
                self.btn_image = pygame.image.load(btn_path).convert_alpha()
        except Exception:
            self.btn_image = None

        # 标题背景图（主页大标题横幅）
        self.title_image = None
        try:
            title_dir = os.path.join(os.path.dirname(__file__), "images")
            for name in ("title.png", "title.jpg", "title.jpeg"):
                p = os.path.join(title_dir, name)
                if os.path.exists(p):
                    # png 用 alpha，jpg 用 convert
                    if name.endswith(".png"):
                        self.title_image = pygame.image.load(p).convert_alpha()
                    else:
                        self.title_image = pygame.image.load(p).convert()
                    break
        except Exception:
            self.title_image = None

        # 悬停提示（技能说明）
        self.hover_card = None            # 当前鼠标悬停的卡牌
        self.hover_start_ms = 0           # 开始悬停的时间戳（ms）
        self.hover_delay_ms = 600         # 悬停多少毫秒后显示提示
        self.mouse_pos = (0, 0)           # 记录鼠标位置用于提示框定位
    
    def _build_card_rects(self, cards: List[Card], y: int) -> List[pygame.Rect]:
        """根据固定卡宽生成等宽矩形；若未固定，则按全卡池计算一次固定卡宽。"""
        rects: List[pygame.Rect] = []
        if not cards:
            return rects
        # 若尚未固定卡宽：按全卡池（1..19）计算一次
        self._ensure_fixed_card_width()
        width: int = cast(int, self.fixed_card_width)

        # 再按统一宽度生成每张卡的矩形
        x = self.card_left
        for _ in cards:
            rects.append(pygame.Rect(x, y, width, self.card_height))
            x += width + self.card_spacing
        return rects

    def _ensure_fixed_card_width(self) -> None:
        """若未设置固定卡宽，则按全卡池（编号 1..19）计算一次并锁定。"""
        if self.fixed_card_width is not None:
            return
        try:
            from game.card_factory import create_card_by_number
        except Exception:
            # 兜底：如果无法导入工厂，则使用默认宽度
            self.fixed_card_width = self.card_width
            return
        max_text_w = 0
        for n in range(1, 20):
            try:
                c = create_card_by_number(n)
            except Exception:
                continue
            text = f"{c.name}({c.points})"
            text_surface = self.font.render(text, True, COLOR_TEXT)
            max_text_w = max(max_text_w, text_surface.get_width())
        self.fixed_card_width = max(self.card_width, max_text_w + 16)
        self._update_card_bg_scaled()

    def fix_card_width_for_round(self) -> None:
        """供小局开始时调用：根据全卡池测量并锁定当局卡宽。"""
        self.fixed_card_width = None
        self._ensure_fixed_card_width()

    def _update_card_bg_scaled(self) -> None:
        """根据当前固定卡宽与卡高，缩放卡牌背景图。"""
        if self.card_bg and self.fixed_card_width:
            try:
                size = (int(self.fixed_card_width), int(self.card_height))
                self.card_bg_scaled = pygame.transform.smoothscale(self.card_bg, size)
            except Exception:
                self.card_bg_scaled = None
        else:
            self.card_bg_scaled = None

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
            self._draw_btn(confirm_rect, "确认", enabled=(len(chosen) == count))

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
        # 与 draw_menu 中的位置保持一致（仅2人可点击）
        banner_rect = pygame.Rect(WINDOW_WIDTH // 2 - 360, 80, 720, 120)
        prompt_y = banner_rect.bottom + 30
        first_btn_y = prompt_y + 60
        rect_2p = pygame.Rect(WINDOW_WIDTH // 2 - 90, first_btn_y, 180, 60)
        if rect_2p.collidepoint(x, y):
            self.selected_num = 2

        # 开始游戏
        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 160, first_btn_y + 3 * 76 + 30, 320, 90)
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
        # 全局背景：若有图则平滑缩放铺满，否则使用纯色
        if self.bg_image:
            if (not self.bg_scaled) or (self.bg_scaled.get_width() != WINDOW_WIDTH or self.bg_scaled.get_height() != WINDOW_HEIGHT):
                try:
                    self.bg_scaled = pygame.transform.smoothscale(self.bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
                except Exception:
                    self.bg_scaled = None
            if self.bg_scaled:
                self.screen.blit(self.bg_scaled, (0, 0))
            else:
                self.screen.fill(COLOR_BG)
        else:
            self.screen.fill(COLOR_BG)
        
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "game" and self.gm:
            # 绘制所有玩家区域
            for idx, player in enumerate(self.gm.players):
                self.draw_player_zones(player, idx, player == self.gm.current_player)

            # 先绘制底部日志框，按钮稍后再画在其上层
            self.draw_log_panel()

            # 绘制出牌/结束回合按钮（在日志之上）
            play_card_rect = pygame.Rect(WINDOW_WIDTH - 300, WINDOW_HEIGHT - 60, 120, 40)
            end_turn_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 60, 120, 40)
            self._draw_btn(play_card_rect, "出牌", enabled=bool(self.selected_card))
            self._draw_btn(end_turn_rect, "结束回合", enabled=True)

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
        """绘制菜单界面（仅显示“2人”按钮，隐藏 3/4 人）"""
        # 顶部大标题“萝卜牌”与标题背景板
        banner_rect = pygame.Rect(WINDOW_WIDTH // 2 - 360, 80, 720, 120)
        # 优先使用图片作为标题背景；无图时退回半透明底
        if self.title_image:
            try:
                banner_img = pygame.transform.smoothscale(self.title_image, (banner_rect.width, banner_rect.height))
                self.screen.blit(banner_img, banner_rect.topleft)
            except Exception:
                banner = pygame.Surface((banner_rect.width, banner_rect.height), pygame.SRCALPHA)
                banner.fill((0, 0, 0, 120))
                self.screen.blit(banner, banner_rect.topleft)
        else:
            banner = pygame.Surface((banner_rect.width, banner_rect.height), pygame.SRCALPHA)
            banner.fill((0, 0, 0, 120))
            self.screen.blit(banner, banner_rect.topleft)
        title_big = self.title_font.render("萝卜牌", True, COLOR_TEXT)
        self.screen.blit(title_big, (
            banner_rect.x + (banner_rect.width - title_big.get_width()) // 2,
            banner_rect.y + (banner_rect.height - title_big.get_height()) // 2,
        ))

        # 提示语下移
        prompt_y = banner_rect.bottom + 30
        title = self.font.render("请选择玩家人数", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, prompt_y))

        # 仅显示“2人”按钮
        first_btn_y = prompt_y + 60
        rect_2p = pygame.Rect(WINDOW_WIDTH // 2 - 90, first_btn_y, 180, 60)
        self._draw_btn(rect_2p, "2人", enabled=True, border=(self.selected_num == 2))

        # “开始游戏”按钮
        start_rect = pygame.Rect(WINDOW_WIDTH // 2 - 160, first_btn_y + 3 * 76 + 30, 320, 90)
        self._draw_btn(start_rect, "开始游戏", enabled=bool(self.selected_num))

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
        self._draw_btn(menu_rect, "返回主页", enabled=True)
        self._draw_btn(exit_rect, "退出游戏", enabled=True)

    def _draw_btn(self, rect: pygame.Rect, text: str, enabled: bool = True, border: bool = False, font: Optional[pygame.font.Font] = None) -> None:
        """绘制通用按钮：使用 btn.png 作为背景并居中文字。
        - enabled=False 时覆盖半透明黑降低亮度。
        - border=True 时绘制高亮边框（用于菜单选择态）。
        """
        # 背景
        if self.btn_image:
            try:
                scaled = pygame.transform.smoothscale(self.btn_image, (rect.width, rect.height))
                self.screen.blit(scaled, rect.topleft)
            except Exception:
                pygame.draw.rect(self.screen, COLOR_ZONE, rect)
        else:
            pygame.draw.rect(self.screen, COLOR_ZONE, rect)

        # 禁用态遮罩
        if not enabled:
            dim = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 110))
            self.screen.blit(dim, rect.topleft)

        # 文字
        use_font = font or self.font
        label = use_font.render(text, True, COLOR_BTN_TEXT)
        text_x = rect.x + (rect.width - label.get_width()) // 2
        text_y = rect.y + (rect.height - label.get_height()) // 2
        self.screen.blit(label, (text_x, text_y))

        # 选中边框
        if border:
            pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, rect, 2)

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
        gap = ZONE_MARGIN
        h_hand, h_battle, h_iso = HAND_HEIGHT, BATTLE_HEIGHT, ISO_HEIGHT
        total_h = h_hand + h_battle + h_iso + gap * 2
        base_y = 50 + idx * (total_h + 30)
        border_color = COLOR_CURRENT if is_current else COLOR_ZONE
        # 如果当前有选中卡牌且需要选择目标，显示玩家区域的可选状态
        if self.selected_card and self.gm and self.gm.current_player:
            current_player = self.gm.current_player
            if self.selected_card.requires_enemy and player != current_player:
                # 对于需要选择敌方的卡牌，其他玩家区域显示为红色
                border_color = (200, 100, 100)  # 红色表示可以选择为目标
            # 不再高亮显示需要卡牌目标的玩家区域

        # 绘制玩家区域边框
        pygame.draw.rect(
            self.screen,
            border_color,
            (140, base_y - 30, WINDOW_WIDTH - 280, total_h + 30),
            2,
        )

        # 用细线分割三个区域（取间隙的中线位置）
        x1, x2 = 140, WINDOW_WIDTH - 140
        y_sep1 = base_y + h_hand + gap // 2
        y_sep2 = base_y + h_hand + gap + h_battle + gap // 2
        sep_color = (120, 120, 120)
        pygame.draw.line(self.screen, sep_color, (x1, y_sep1), (x2, y_sep1), 1)
        pygame.draw.line(self.screen, sep_color, (x1, y_sep2), (x2, y_sep2), 1)

        # 绘制各个区域
        self.draw_zone("手牌", player.hand, player, "hand", base_y, h_hand)
        self.draw_zone("战场", player.battlefield_cards, player, "battlefield", base_y + h_hand + gap, h_battle)
        self.draw_zone("孤立", player.isolated_cards, player, "isolated", base_y + h_hand + gap + h_battle + gap, h_iso)

        # 绘制玩家信息（在board左侧分行显示，避免遮挡牌）
        live_score = self.compute_live_score(player)
        info_x = 60
        info_y = base_y - 20
        name_surf = self.font.render(player.name, True, COLOR_TEXT)
        score_surf = self.small_font.render(f"分数: {live_score}", True, COLOR_TEXT)
        wins_surf = self.small_font.render(f"胜局: {player.wins}", True, COLOR_TEXT)
        self.screen.blit(name_surf, (info_x, info_y))
        self.screen.blit(score_surf, (info_x, info_y + 22))
        self.screen.blit(wins_surf, (info_x, info_y + 42))

        # 如果是选中的目标，绘制高亮边框
        if player in self.target_list:
            highlight_color = (255, 0, 0) if player in self.enemy_list else (0, 255, 0)
            pygame.draw.rect(
                self.screen,
                highlight_color,
                (140, base_y - 30, WINDOW_WIDTH - 280, total_h + 30),
                4,
            )

    def draw_log_panel(self) -> None:
        """在底部绘制一个日志框，显示最近的操作。"""
        panel_height = 90
        panel_rect = pygame.Rect(0, WINDOW_HEIGHT - panel_height, WINDOW_WIDTH, panel_height)
        pygame.draw.rect(self.screen, (20, 20, 20), panel_rect)
        pygame.draw.rect(self.screen, (80, 80, 80), panel_rect, 2)

        # 面板与按钮约束
        panel_top = WINDOW_HEIGHT - panel_height
        bottom_safe_y = WINDOW_HEIGHT - 70  # 按钮上沿之上留出安全距离
        line_h = self.small_font.get_height() + 2

        # 在空间足够时绘制标题；不足则让出空间给日志
        title_surface = self.small_font.render("操作记录", True, COLOR_TEXT)
        title_h = title_surface.get_height()
        # 预估最小需要高度：标题 + 一行日志
        need_for_title_and_one = 8 + title_h + 4 + line_h
        avail = bottom_safe_y - panel_top
        draw_title = avail >= need_for_title_and_one

        y_title = panel_top + 8
        if draw_title:
            self.screen.blit(title_surface, (10, y_title))
            logs_top = y_title + title_h + 4
        else:
            logs_top = panel_top + 6

        # 取最后若干条日志，自底向上绘制，保证至少尝试一行
        lines = self.logs[-self.max_logs:]
        if not lines:
            return
        # 从底部向上画，直到触达 logs_top
        drawn = 0
        for i, line in enumerate(reversed(lines)):
            text_surface = self.small_font.render(line, True, COLOR_TEXT)
            y = bottom_safe_y - (i + 1) * line_h
            if y < logs_top:
                break
            self.screen.blit(text_surface, (10, y))
            drawn += 1
        # 如果一行都没画出来（空间极其有限），强制在 logs_top 位置画一行
        if drawn == 0:
            text_surface = self.small_font.render(lines[-1], True, COLOR_TEXT)
            self.screen.blit(text_surface, (10, logs_top))

    def draw_zone(self, label: str, cards: List[Card], player: Player, zone_name: str, y: int, height: int = ZONE_HEIGHT) -> None:
        """绘制卡牌区域（仅大号水印 + 卡牌）"""
        zone_rect = pygame.Rect(140, y, WINDOW_WIDTH - 280, height)

        # 中心水印（放大字号、低透明度）
        wm = self.wm_font.render(label, True, (220, 220, 220))
        wm.set_alpha(40)
        wm_x = zone_rect.x + (zone_rect.width - wm.get_width()) // 2
        wm_y = zone_rect.y + (zone_rect.height - wm.get_height()) // 2
        self.screen.blit(wm, (wm_x, wm_y))

        rects = self._build_card_rects(cards, y)
        for card, rect in zip(cards, rects):
            # 背景：使用卡牌背景图；若无则使用灰色填充
            if self.card_bg_scaled:
                self.screen.blit(self.card_bg_scaled, rect.topleft)
            else:
                pygame.draw.rect(self.screen, (80, 80, 80), rect)

            # 文字可读性（更柔和）：浅色渐变叠加 + 轻微描边阴影，而非纯黑遮罩
            # 顶部标题区域：从透明过渡到浅白（不破坏背景饱和度）
            title_band_h = 26
            if title_band_h > 0:
                title_grad = pygame.Surface((rect.width - 10, title_band_h), pygame.SRCALPHA)
                for i in range(title_band_h):
                    alpha = int(60 * (i / max(1, title_band_h - 1)))  # 0 -> 60
                    pygame.draw.line(title_grad, (255, 255, 255, alpha), (0, i), (rect.width - 10, i))
                self.screen.blit(title_grad, (rect.x + 5, rect.y + 4))

            # 技能区域：从透明到更轻的浅白，避免压暗背景
            line_y_start = rect.y + 35
            skill_band_h = max(0, rect.height - (line_y_start - rect.y) - 6)
            if skill_band_h > 0:
                skill_grad = pygame.Surface((rect.width - 10, skill_band_h), pygame.SRCALPHA)
                for i in range(skill_band_h):
                    alpha = int(40 * (i / max(1, skill_band_h - 1)))  # 0 -> 40
                    pygame.draw.line(skill_grad, (255, 255, 255, alpha), (0, i), (rect.width - 10, i))
                self.screen.blit(skill_grad, (rect.x + 5, line_y_start))

            # 边框颜色（状态反馈，采用更高对比度并加粗）
            if card == self.selected_card:
                border_color = (255, 200, 0)  # 选中：金色
                border_thick = 3
            elif card in self.target_list:
                border_color = (50, 220, 120)  # 目标：明亮绿
                border_thick = 3
            else:
                # 普通：浅灰
                border_color = (180, 180, 180)
                border_thick = 2
            pygame.draw.rect(self.screen, border_color, rect, border_thick)

            # 如果鼠标悬停在卡牌上（进一步强调）
            if hasattr(card, "highlight") and card.highlight:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 3)

            # 绘制卡牌基本信息（卡名必须完整显示，卡片宽度已动态调整）
            card_info = f"{card.name}({card.points})"
            # 不再在卡牌前加“[孤]”标记
            card_text = self.font.render(card_info, True, COLOR_CARD_TEXT)
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
                    skill_text = self.small_font.render(line, True, COLOR_CARD_TEXT)
                    self.screen.blit(skill_text, (rect.x + 5, line_y_start + j * line_h))

    def check_click_card(self, player: Player, x: int, y: int, zone: str = "hand") -> Optional[Card]:
        """检查是否点击到卡牌
        
        :param zone: 要检查的区域，可以是 "hand"/"battlefield"/"isolated"
        """
        cards: List[Card] = []
        gap = ZONE_MARGIN
        h_hand, h_battle, h_iso = HAND_HEIGHT, BATTLE_HEIGHT, ISO_HEIGHT
        total_h = h_hand + h_battle + h_iso + gap * 2
        base_y = 50 + player.index * (total_h + 30)

        if zone == "hand":
            cards = player.hand
            y_offset = 0
        elif zone == "battlefield":
            cards = player.battlefield_cards
            y_offset = h_hand + gap
        elif zone == "isolated":
            cards = player.isolated_cards
            y_offset = h_hand + gap + h_battle + gap
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
        gap = ZONE_MARGIN
        h_hand, h_battle, h_iso = HAND_HEIGHT, BATTLE_HEIGHT, ISO_HEIGHT
        total_h = h_hand + h_battle + h_iso + gap * 2
        for player in self.gm.players:
            base_y = 50 + player.index * (total_h + 30)
            rect = pygame.Rect(140, base_y - 30, WINDOW_WIDTH - 280, total_h + 30)
            if rect.collidepoint(x, y):
                return player
        return None

    def get_card_rect_for_card(self, card: Card, player: Player, zone: str = "hand") -> Optional[pygame.Rect]:
        """获取卡牌的矩形区域
        
        :param zone: 要检查的区域，可以是 "hand"/"battlefield"/"isolated"
        """
        gap = ZONE_MARGIN
        h_hand, h_battle, h_iso = HAND_HEIGHT, BATTLE_HEIGHT, ISO_HEIGHT
        total_h = h_hand + h_battle + h_iso + gap * 2
        base_y = 50 + player.index * (total_h + 30)
        
        # 确定要搜索的卡牌列表和纵向偏移
        if zone == "hand":
            cards = player.hand
            y_offset = 0
        elif zone == "battlefield":
            cards = player.battlefield_cards
            y_offset = h_hand + gap
        elif zone == "isolated":
            cards = player.isolated_cards
            y_offset = h_hand + gap + h_battle + gap
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
