"""
改进版：Skill 基类 + Skill_1 ~ Skill_10 + PlayAction

我对以下内容做了修改并在代码中用 "# >>> CHANGED" 标记出来：
  - 新增 PlayAction（承载 manager 与 enemies）
  - Skill 基类增加 validate_enemies / needs_enemy / 相关注释
  - Skill_9 修正为使用 enemies（双方掷骰子），删除原先的 discard_choice 逻辑
  - Skill_6 保持使用 action.manager.draw_card_for_player（需要在创建 PlayAction 时传入 manager）

请在代码中搜索 "# >>> CHANGED" 查看我改动的地方。
"""

from abc import ABC, abstractmethod
import random

# -------------------- 技能基类 --------------------
class Skill(ABC):
    def __init__(self, name=None, targets_required=0, enemy_required=0, target_side="self", target_type="hand"):
        """
        :param name: 技能名称
        :param targets_required: 需要多少张牌作为目标（牌目标）
        :param enemy_required: 需要多少个敌人作为目标（玩家目标）
        :param target_side: 目标牌是 哪个玩家的
            - "self"   自己
            - "other"  只能选择其他玩家
            - "any"    自己和他人都可以
        :param target_type : 手牌hand/场上牌battlefield/无none 不能是孤立牌
        """
        self.name = name or self.__class__.__name__
        self.targets_required = targets_required
        self.enemy_required = enemy_required
        self.target_side = target_side
        self.target_type = target_type

    @property
    def needs_target(self):
        return self.targets_required > 0

    @property
    def needs_enemy(self):
        return self.enemy_required > 0

    def validate_targets(self, action):
        """验证牌目标（card targets）"""
        if self.targets_required == 0:
            return []
        if not action.targets or len(action.targets) < self.targets_required:
            raise ValueError(f"{self.name} 需要 {self.targets_required} 个牌目标，但传入 {action.targets}")
        return action.targets

    # >>> CHANGED: 新增验证敌人目标的方法
    def validate_enemies(self, action):
        """验证敌方玩家目标（enemy targets）"""
        if self.enemy_required == 0:
            return []
        if not action.enemies or len(action.enemies) < self.enemy_required:
            raise ValueError(f"{self.name} 需要 {self.enemy_required} 个敌方玩家目标，但传入 {action.enemies}")
        return action.enemies
    # <<< CHANGED

    @abstractmethod
    def apply(self, action):
        """技能生效逻辑（由子类实现）"""
        pass

    def __str__(self):
        return self.name


# -------------------- 技能实现 --------------------

class Skill_1(Skill):
    """本牌上场时，根据己方场上牌数给自己加分"""
    def __init__(self):
        super().__init__("场上加点", targets_required=0, target_side="self", target_type="battlefield")

    def apply(self, action):
        cards_on_board = action.board.get_player_zone(action.owner, "battlefield")
        action.self_card.points += len(cards_on_board)
        msg = f"[{self.name}] {action.self_card.name} 点数增加到 {action.self_card.points}"
        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)


class Skill_2(Skill):
    """如果自己战场上只有这张牌，则给这张牌加5点"""
    def __init__(self):
        super().__init__("孤胆勇士", targets_required=0, target_side="self", target_type="battlefield")

    def apply(self, action):
        cards_on_board = action.board.get_player_zone(action.owner, "battlefield")
        if len(cards_on_board) == 1 and cards_on_board[0] == action.self_card:
            action.self_card.points += 4
            msg = f"[{self.name}] {action.self_card.name} 点数增加到 {action.self_card.points}"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)


class Skill_3(Skill):
    """给场上指定的一张牌加2点"""
    def __init__(self):
        super().__init__("援助", targets_required=1, target_side="any", target_type="battlefield")

    def apply(self, action):
        # 首先获取目标牌所在的玩家区域
        targets = self.validate_targets(action)
        if not targets:
            msg = f"[{self.name}] 错误：没有选择目标卡牌"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)
            return

        target_card = targets[0]
        target_player = None

        # 查找目标卡牌所属的玩家
        for player in action.board.players:
            cards = action.board.get_player_zone(player, "battlefield")
            if target_card in cards:
                target_player = player
                break

        if not target_player:
            msg = f"[{self.name}] 错误：找不到目标卡牌所属的玩家"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)
            return
        
        # 执行援助效果
        target_card.points += 2
        msg = f"[{self.name}] {target_player.name}的{target_card.name}被加2点，现在{target_card.points}点"
        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)


class Skill_4(Skill):
    """如果上一小局玩家获胜，则该玩家得分增加固定分数（加到玩家score）"""
    def __init__(self, points=3):
        super().__init__("胜利加分", targets_required=0, target_side="self")
        self.points = points

    def apply(self, action):
        if getattr(action.owner, "prev_round_won", False):
            action.owner.score += self.points
            msg = f"[{self.name}] {action.owner.name} 得分 +{self.points}，总分 {action.owner.score}"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)


class Skill_5(Skill):
    """如果这张牌的使用者上一回合输了，则他得到 +3 分"""
    def __init__(self):
        super().__init__("安慰奖", targets_required=0, target_side="self")

    def apply(self, action):
        if not getattr(action.owner, "prev_round_won", False):
            action.owner.score += 3
            msg = f"[{self.name}] {action.owner.name} 上一回合失败，获得安慰奖 +3，总分 {action.owner.score}"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)


class Skill_6(Skill):
    """抽取一张牌到手牌区（注意：使用 action.manager）"""
    def __init__(self):
        super().__init__("摸牌", targets_required=0, target_side="self", target_type="none")

    def apply(self, action):
        if not getattr(action, 'manager', None):
            raise RuntimeError(f"{self.name} 需要 PlayAction.manager 来抽牌，请在创建 PlayAction 时传入 game manager")
        new_card = action.manager.draw_card_for_player(action.owner)
        if new_card:
            action.owner.hand.append(new_card)
            msg = f"[{self.name}] {action.owner.name} 抽到 {new_card.name}"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)
        else:
            msg = f"[{self.name}] {action.owner.name} 没有抽到牌"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)


class Skill_7(Skill):
    """消灭敌方场上的一张指定牌"""
    def __init__(self):
        super().__init__("精准打击", targets_required=1, target_side="other", target_type="battlefield")

    def apply(self, action):
        target_card = self.validate_targets(action)[0]
        for player in action.board.players:
            zone = action.board.get_player_zone(player, "battlefield")
            if target_card in zone:
                zone.remove(target_card)
                msg = f"[{self.name}] 消灭了 {player.name} 的 {target_card.name}"
                if getattr(action, 'ui', None):
                    action.ui.add_log(msg)
                else:
                    print(msg)
                break


class Skill_8(Skill):
    """己方战场已有几张8 → 本牌点数 +3 * 数量"""
    def __init__(self):
        super().__init__("同伴羁绊", targets_required=0, target_side="self", target_type="battlefield")

    def apply(self, action):
        cards_on_board = action.board.get_player_zone(action.owner, "battlefield")
        count_8 = sum(1 for c in cards_on_board if c.name == "8" and c != action.self_card)
        if count_8 > 0:
            action.self_card.points += 3 * count_8
            msg = f"[{self.name}] {action.self_card.name} 技能触发，加点后 {action.self_card.points}"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)


class Skill_9(Skill):
    """
    拼点：选择一个目标玩家（enemy），双方掷骰子比较点数
    - 胜者摸一张牌
    - 败者弃一张手牌（如果有）
    """
    def __init__(self):
        # >>> CHANGED: 将 targets_required 设为0（不需要牌目标），enemy_required=1（需要选一个敌人）
        super().__init__("拼点", targets_required=0, enemy_required=1, target_side="other", target_type="none")

    def apply(self, action):
        # >>> CHANGED: 使用 validate_enemies 取出目标玩家
        target_player = self.validate_enemies(action)[0]

        owner_point = random.randint(1, 6)
        target_point = random.randint(1, 6)
        msg = f"[{self.name}] 拼点 {action.owner.name} 掷出 {owner_point} vs {target_player.name} 掷出 {target_point}"
        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)

        if owner_point > target_point:
            # 出牌者获胜 → 出牌者摸牌，目标弃牌
            if not getattr(action, 'manager', None):
                raise RuntimeError(f"{self.name} 需要 PlayAction.manager 来抽牌，请在创建 PlayAction 时传入 game manager")
            new_card = action.manager.draw_card_for_player(action.owner)
            action.owner.hand.append(new_card)
            msg = f"[{self.name}] {action.owner.name} 获胜，抽到 {new_card.name}"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)

            if target_player.hand:
                discarded = random.choice(target_player.hand)
                target_player.hand.remove(discarded)
                msg = f"[{self.name}] {target_player.name} 弃掉 {discarded.name}"
                if getattr(action, 'ui', None): action.ui.add_log(msg)
                else: print(msg)

        elif owner_point < target_point:
            # 目标获胜 → 目标摸牌，出牌者弃牌
            if not getattr(action, 'manager', None):
                raise RuntimeError(f"{self.name} 需要 PlayAction.manager 来抽牌，请在创建 PlayAction 时传入 game manager")
            new_card = action.manager.draw_card_for_player(target_player)
            target_player.hand.append(new_card)
            msg = f"[{self.name}] {target_player.name} 获胜，抽到 {new_card.name}"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)

            if action.owner.hand:
                discarded = random.choice(action.owner.hand)
                action.owner.hand.remove(discarded)
                msg = f"[{self.name}] {action.owner.name} 弃掉 {discarded.name}"
                if getattr(action, 'ui', None): action.ui.add_log(msg)
                else: print(msg)

        else:
            msg = f"[{self.name}] 平局，无事发生"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)


class Skill_10(Skill):
    """出牌时给自己增加 1-6 的随机点数"""
    def __init__(self):
        super().__init__("随机加点", targets_required=0, target_side="self")

    def apply(self, action):
        rand_points = random.randint(1, 6)
        action.self_card.points += rand_points
        msg = f"[{self.name}] {action.self_card.name} 随机加 {rand_points} 点，现在 {action.self_card.points}"
        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)

class Skill_11(Skill):
    """
    弃掉自己手上所有手牌，然后抽取等量的新牌
    """
    def __init__(self):
        super().__init__("手牌重置", targets_required=0, target_side="self", target_type="hand")

    def apply(self, action):
        if not getattr(action, 'manager', None):
            raise RuntimeError(f"{self.name} 需要 PlayAction.manager 来抽牌，请在创建 PlayAction 时传入 game manager")

        hand_size = len(action.owner.hand)
        if hand_size == 0:
            msg = f"[{self.name}] {action.owner.name} 没有手牌，无法触发效果"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)
            return

        # 弃掉所有手牌
        discarded_cards = list(action.owner.hand)  # 复制以便打印
        action.owner.hand.clear()

        # 抽取等量新牌
        new_cards = []
        for _ in range(hand_size):
            new_card = action.manager.draw_card_for_player(action.owner)
            if new_card:
                action.owner.hand.append(new_card)
                new_cards.append(new_card)

        msg = (f"[{self.name}] {action.owner.name} 弃掉了 {', '.join(c.name for c in discarded_cards)}，"
               f"并抽取了 {len(new_cards)} 张新牌：{', '.join(c.name for c in new_cards)}")
        if getattr(action, 'ui', None): action.ui.add_log(msg)
        else: print(msg)

class Skill_16(Skill):
    """抽取两张牌到手牌区"""
    def __init__(self):
        super().__init__("双抽", targets_required=0, target_side="self", target_type="none")

    def apply(self, action):
        if not getattr(action, 'manager', None):
            raise RuntimeError(f"{self.name} 需要 PlayAction.manager 来抽牌，请在创建 PlayAction 时传入 game manager")

        new_cards = []
        for _ in range(2):  # 抽两张牌
            card = action.manager.draw_card_for_player(action.owner)
            if card:
                action.owner.hand.append(card)
                new_cards.append(card)

        if new_cards:
            msg = f"[{self.name}] {action.owner.name} 抽到 {', '.join(c.name for c in new_cards)}"
        else:
            msg = f"[{self.name}] {action.owner.name} 没有抽到牌"

        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)

class Skill_21(Skill):
    """选择一名玩家的战场牌，使其点数翻倍"""
    def __init__(self):
        super().__init__("加倍打击", targets_required=1, target_side="any", target_type="battlefield")

    def apply(self, action):
        # 获取目标牌
        targets = self.validate_targets(action)
        if not targets:
            msg = f"[{self.name}] 没有选择目标卡牌"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)
            return

        target_card = targets[0]

        # 查找目标牌所属玩家
        target_player = None
        for player in action.board.players:
            if target_card in action.board.get_player_zone(player, "battlefield"):
                target_player = player
                break

        if not target_player:
            msg = f"[{self.name}] 找不到目标卡牌所属玩家"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)
            return

        # 执行翻倍效果
        old_points = target_card.points
        target_card.points *= 2
        msg = f"[{self.name}] {target_player.name} 的 {target_card.name} 点数 {old_points} -> {target_card.points}"
        if getattr(action, 'ui', None): action.ui.add_log(msg)
        else: print(msg)

class Skill_23(Skill):
    """出牌时，点数增加玩家手牌数，但最多增加5点"""
    def __init__(self):
        super().__init__("手牌加成", targets_required=0, target_side="self")

    def apply(self, action):
        owner = action.owner
        hand_count = len(owner.hand)
        increment = min(hand_count, 5)  # 限制最多加5点
        action.self_card.points += increment
        msg = f"[{self.name}] {action.self_card.name} 出牌触发，手牌数 {hand_count}，点数增加 {increment} 到 {action.self_card.points}"
        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)

class Skill_26(Skill):
    """出牌时，选择一名敌人玩家，随机抽取一张手牌加入自己手牌区"""
    def __init__(self):
        super().__init__("掠夺", targets_required=0, enemy_required=1, target_side="other")

    def apply(self, action):
        # 验证并获取目标敌人
        target_player = self.validate_enemies(action)[0]

        if not target_player.hand:
            msg = f"[{self.name}] {target_player.name} 没有手牌可抽"
            if getattr(action, 'ui', None): 
                action.ui.add_log(msg)
            else: 
                print(msg)
            return

        # 随机选择一张手牌
        stolen_card = random.choice(target_player.hand)
        target_player.hand.remove(stolen_card)
        action.owner.hand.append(stolen_card)

        msg = f"[{self.name}] {action.owner.name} 从 {target_player.name} 手牌中抽取 {stolen_card.name}"
        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)

class Skill_27(Skill):
    """敌人战场牌数多于自己时，选择任意玩家的战场牌+3"""
    def __init__(self):
        super().__init__("战场优势加点", targets_required=1, enemy_required=1, target_side="any", target_type="battlefield")

    def apply(self, action):
        # 验证敌人目标
        enemy = self.validate_enemies(action)[0]

        player_board_count = len(action.board.get_player_zone(action.owner, "battlefield"))
        enemy_board_count = len(action.board.get_player_zone(enemy, "battlefield"))

        if enemy_board_count > player_board_count:
            # 验证玩家选择的目标牌
            targets = self.validate_targets(action)
            if not targets:
                msg = f"[{self.name}] 错误：没有选择目标卡牌"
                if getattr(action, 'ui', None): action.ui.add_log(msg)
                else: print(msg)
                return

            target_card = targets[0]
            target_card.points += 3
            msg = f"[{self.name}] {target_card.name} 被加 3 点，当前点数 {target_card.points}"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)
        else:
            msg = f"[{self.name}] 条件不满足，{enemy.name} 战场牌数 ({enemy_board_count}) ≤ {action.owner.name} 战场牌数 ({player_board_count})"
            if getattr(action, 'ui', None): action.ui.add_log(msg)
            else: print(msg)

class Skill_28(Skill):
    """玩家打出这张牌，先抽两张牌到手牌，再弃掉自己选择的两张牌"""
    def __init__(self):
        # 改为出牌前不要求目标，出牌后在 UI 中选择要弃的两张手牌
        super().__init__("先抽再弃", targets_required=0, target_side="self", target_type="none")

    def apply(self, action):
        # --- 第一步：抽两张牌 ---
        if not getattr(action, 'manager', None):
            raise RuntimeError(f"{self.name} 需要 PlayAction.manager 来抽牌")

        new_cards = []
        for _ in range(2):
            new_card = action.manager.draw_card_for_player(action.owner)
            if new_card:
                action.owner.hand.append(new_card)
                new_cards.append(new_card)

        if new_cards:
            msg = f"[{self.name}] {action.owner.name} 抽到 {[c.name for c in new_cards]}"
        else:
            msg = f"[{self.name}] 未能抽到新牌"
        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)

        # --- 第二步：弃掉玩家选择的两张牌（在抽牌后进行选择） ---
        discard_cards = []
        ui = getattr(action, 'ui', None)
        owner = action.owner
        # 如果有 UI，弹出专用选择器让玩家从当前手牌中选择两张弃掉
        if ui and hasattr(ui, 'select_cards_from_hand'):
            prompt = "请选择要弃掉的两张手牌（再次点击可取消选择），然后点击确认"
            try:
                discard_cards = ui.select_cards_from_hand(owner, 2, prompt)
            except Exception as e:
                # 回退到随机选择
                discard_cards = []
        # 无 UI 或选择失败时，随机弃置（尽力而为）
        if not discard_cards:
            take_n = min(2, len(owner.hand))
            import random as _r
            discard_cards = _r.sample(owner.hand, take_n) if take_n > 0 else []

        for c in discard_cards:
            if c in owner.hand:
                owner.hand.remove(c)
                msg = f"[{self.name}] {owner.name} 弃掉 {c.name}"
                if ui:
                    ui.add_log(msg)
                else:
                    print(msg)

class Skill_29(Skill):
    """选择一名敌人，敌方战场比自己多的牌数 -> 本牌点数+1/张"""
    def __init__(self):
        super().__init__("战场压制", targets_required=0, enemy_required=1, target_side="other", target_type="battlefield")

    def apply(self, action):
        target_player = self.validate_enemies(action)[0]
        owner = action.owner
        owner_board_count = len(owner.battlefield_cards)
        target_board_count = len(target_player.battlefield_cards)
        diff = target_board_count - owner_board_count

        if diff > 0:
            action.self_card.points += diff
            msg = f"[{self.name}] {action.self_card.name} 点数增加 {diff}，现在 {action.self_card.points}"
        else:
            msg = f"[{self.name}] 技能无法生效：{target_player.name} 战场牌数不多于 {owner.name}"

        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)

class Skill_35(Skill):
    """打出这张牌放入孤立区，同时玩家获得一张同名牌"""
    def __init__(self):
        super().__init__("孤立放置", targets_required=0, enemy_required=0, target_side="self", target_type="none")

    def apply(self, action):
        owner = action.owner
        card = action.self_card

        # 如果错误地在战场中，移除之
        if card in owner.battlefield_cards:
            owner.battlefield_cards.remove(card)

        # 放入孤立区（确保只存在一次）
        if card not in owner.isolated_cards:
            owner.isolated_cards.append(card)

        # 玩家再获得一张同名牌
        try:
            owner.hand.append(card)
            msg = f"[{self.name}] {card.name} 被放入孤立区，同时 {owner.name} 获得一张同名牌 {card.name}"
        except Exception:
            # 如果实例化失败，则仅提示放入孤立区
            msg = f"[{self.name}] {card.name} 被放入孤立区，但无法生成新牌"

        if getattr(action, 'ui', None):
            action.ui.add_log(msg)
        else:
            print(msg)

