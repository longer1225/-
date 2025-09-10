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
        :param target_side: 目标是 哪个玩家
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
            action.self_card.points += 5
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
