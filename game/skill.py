from abc import ABC, abstractmethod
import random

# -------------------- 技能基类 --------------------
class Skill(ABC):
    def __init__(self, name=None, targets_required=0, target_side="self",target_type="hand"):
        """
        :param name: 技能名称
        :param targets_required: 需要多少张牌作为目标
        :param target_side: 目标归属
            - "self"   只能选择自己
            - "other"  只能选择其他玩家
            - "any"    自己和他人都可以
        """
        self.name = name or self.__class__.__name__
        self.targets_required = targets_required
        self.target_side = target_side
        self.target_type = target_type

    @property
    def needs_target(self):
        return self.targets_required > 0

    def validate_targets(self, action):
        if self.targets_required == 0:
            return []
        if not action.targets or len(action.targets) < self.targets_required:
            raise ValueError(f"{self.name} 需要 {self.targets_required} 个目标，但传入 {action.targets}")
        return action.targets

    @abstractmethod
    def apply(self, action):
        """技能生效逻辑"""
        pass

    def __str__(self):
        return self.name


# -------------------- 技能实现 --------------------

class Skill_1(Skill):
    """本牌上场时，根据己方场上牌数给自己加分"""
    def __init__(self):
        super().__init__("场上加点", targets_required=0, target_side="self")

    def apply(self, action):
        cards_on_board = action.board.get_player_zone(action.owner,"battlefield")
        action.self_card.points += len(cards_on_board)
        print(f"[{self.name}] {action.self_card.name} 点数增加到 {action.self_card.points}")


class Skill_2(Skill):
    """如果自己战场上只有这张牌，则给这张牌加5点"""
    def __init__(self):
        super().__init__("孤胆勇士", targets_required=0, target_side="self")

    def apply(self, action):
        cards_on_board = action.board.get_player_zone(action.owner,"battlefield")
        if len(cards_on_board) == 1 and cards_on_board[0] == action.self_card:
            action.self_card.points += 5
            print(f"[{self.name}] {action.self_card.name} 点数增加到 {action.self_card.points}")


class Skill_3(Skill):
    """给场上指定的一张牌加2点"""
    def __init__(self):
        super().__init__("援助", targets_required=1, target_side="any")

    def apply(self, action):
        target_card = self.validate_targets(action)[0]
        target_card.points += 2
        print(f"[{self.name}] {target_card.name} 被加2点，现在 {target_card.points}")


class Skill_4(Skill):
    """如果上一小局玩家获胜，则该玩家得分增加固定分数"""
    def __init__(self, points=3):
        super().__init__("胜利加分", targets_required=0, target_side="self")
        self.points = points

    def apply(self, action):
        if getattr(action.owner, "prev_round_won", False):
            action.owner.score += self.points
            print(f"[{self.name}] {action.owner.name} 得分 +{self.points}，总分 {action.owner.score}")


class Skill_5(Skill):
    """上一回合输的玩家得到 +3 分"""
    def __init__(self):
        super().__init__("安慰奖", targets_required=0, target_side="any")

    def apply(self, action):
        for player in action.board.players:
            if not getattr(player, "prev_round_won", False):
                player.score += 3
                print(f"[{self.name}] {player.name} 输家加3分，总分 {player.score}")


class Skill_6(Skill):
    """抽取一张牌到手牌区"""
    def __init__(self):
        super().__init__("摸牌", targets_required=0, target_side="self")

    def apply(self, action):
        new_card = action.board.manager.draw_card_for_player(action.owner)
        action.owner.hand.append(new_card)
        print(f"[{self.name}] {action.owner.name} 抽到 {new_card.name}")


class Skill_7(Skill):
    """消灭敌方场上的一张指定牌"""
    def __init__(self):
        super().__init__("精准打击", targets_required=1, target_side="other")

    def apply(self, action):
        target_card = self.validate_targets(action)[0]
        for player in action.board.players:
            if target_card in action.board.get_player_zone(action.target,"battlefield"):
                action.board.get_player_zone(player).remove(target_card)
                print(f"[{self.name}] 消灭了 {player.name} 的 {target_card.name}")
                break


class Skill_8(Skill):
    """己方战场已有几张8 → 本牌点数 +3 * 数量"""
    def __init__(self):
        super().__init__("同伴羁绊", targets_required=0, target_side="self")

    def apply(self, action):
        cards_on_board = action.board.get_player_zone(action.owner)
        count_8 = sum(1 for c in cards_on_board if c.name == "8" and c != action.self_card)
        if count_8 > 0:
            action.self_card.points += 3 * count_8
            print(f"[{self.name}] {action.self_card.name} 技能触发，加点后 {action.self_card.points}")


class Skill_9(Skill):
    """
    拼点：选择一个目标玩家 + 一张弃掉的牌
    """
    def __init__(self):
        super().__init__("拼点", targets_required=2, target_side="any")  # [目标玩家, 弃掉的牌]

    def apply(self, action):
        target_player, discard_choice = self.validate_targets(action)

        owner_point = random.randint(1, 6)
        target_point = random.randint(1, 6)
        print(f"[{self.name}] 拼点 {action.owner.name} {owner_point} vs {target_player.name} {target_point}")

        if owner_point > target_point:
            action.owner.draw_card_random()
            if discard_choice in target_player.hand:
                target_player.hand.remove(discard_choice)
                print(f"[{self.name}] {target_player.name} 弃掉 {discard_choice.name}")
        elif owner_point < target_point:
            target_player.draw_card_random()
            if discard_choice in action.owner.hand:
                action.owner.hand.remove(discard_choice)
                print(f"[{self.name}] {action.owner.name} 弃掉 {discard_choice.name}")
        else:
            print(f"[{self.name}] 拼点平局，无事发生")


class Skill_10(Skill):
    """出牌时给自己增加 1-6 的随机点数"""
    def __init__(self):
        super().__init__("随机加点", targets_required=0, target_side="self")

    def apply(self, action):
        rand_points = random.randint(1, 6)
        action.self_card.points += rand_points
        print(f"[{self.name}] {action.self_card.name} 随机加 {rand_points} 点，现在 {action.self_card.points}")
