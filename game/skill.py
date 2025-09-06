from abc import ABC, abstractmethod
import random

class Skill(ABC):
    """
    技能抽象基类，所有技能必须继承此类并实现 apply 方法。
    """
    targets_required = 0  # 默认不需要目标

    @abstractmethod
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        pass

    def __str__(self):
        return self.__class__.__name__


# -------------------- 技能实现 --------------------

class Skill_1(Skill):
    """本牌上场时，根据己方场上牌数给自己加分"""
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        cards_on_board = board.get_player_board(owner)
        self_card.points += len(cards_on_board)
        print(f"{self_card.name} 技能1触发，点数增加到 {self_card.points}")


class Skill_2(Skill):
    """如果自己战场上只有这张牌，则给这张牌加5点"""
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        cards_on_board = board.get_player_board(owner)
        if len(cards_on_board) == 1 and cards_on_board[0] == self_card:
            self_card.points += 5
            print(f"{self_card.name} 技能2触发，点数增加到 {self_card.points}")


class Skill_3(Skill):
    """给场上指定的一张牌加2点"""
    targets_required = 1
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        target_card = targets[0]
        target_card.points += 2
        print(f"{target_card.name} 技能3触发，被加2点，现在 {target_card.points}")


class Skill_4(Skill):
    """如果上一小局玩家获胜，则该玩家得分增加固定分数"""
    def __init__(self, points=3):
        self.points = points
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        if getattr(owner, "prev_round_won", False):
            owner.score += self.points
            print(f"{owner.name} 技能4触发，得分 +{self.points}，总分 {owner.score}")


class Skill_5(Skill):
    """上一回合输的玩家得到 +3 分"""
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        for player in board.players:
            if not getattr(player, "prev_round_won", False):
                player.score += 3
                print(f"{player.name} 技能5触发，输家加3分，总分 {player.score}")


class Skill_6(Skill):
    """抽取一张牌到手牌区"""
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        new_card = board.manager.draw_card_for_player(owner)
        owner.hand.append(new_card)
        print(f"{owner.name} 技能6触发，抽到 {new_card.name}")


class Skill_7(Skill):
    """消灭敌方场上的一张指定牌"""
    targets_required = 1
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        target_card = targets[0]
        for player in board.players:
            if target_card in board.get_player_board(player):
                board.get_player_board(player).remove(target_card)
                print(f"{owner.name} 技能7触发，消灭了 {player.name} 的 {target_card.name}")
                break


class Skill_8(Skill):
    """己方战场已有几张8 → 本牌点数 +3 * 数量"""
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        cards_on_board = board.get_player_board(owner)
        count_8 = sum(1 for c in cards_on_board if c.name == "8" and c != self_card)
        if count_8 > 0:
            self_card.points += 3 * count_8
            print(f"{self_card.name} 技能8触发，已有 {count_8} 张8，加点后 {self_card.points}")


class Skill_9(Skill):
    """
    拼点：选择一个目标玩家
    - 胜者抽牌
    - 败者弃牌
    """
    targets_required = 2  # [目标玩家, 弃掉的牌]

    def apply(self, owner=None, board=None, self_card=None, targets=None):
        target_player = targets[0]
        discard_choice = targets[1]

        owner_point = random.randint(1, 6)
        target_point = random.randint(1, 6)
        print(f"{owner.name} 拼点 {owner_point} vs {target_player.name} {target_point}")

        if owner_point > target_point:
            owner.draw_card_random()
            if discard_choice in target_player.hand:
                target_player.hand.remove(discard_choice)
                print(f"{target_player.name} 弃掉 {discard_choice.name}")
        elif owner_point < target_point:
            target_player.draw_card_random()
            if discard_choice in owner.hand:
                owner.hand.remove(discard_choice)
                print(f"{owner.name} 弃掉 {discard_choice.name}")
        else:
            print("拼点平局，无事发生")


class Skill_10(Skill):
    """出牌时给自己增加 1-6 的随机点数"""
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        rand_points = random.randint(1, 6)
        self_card.points += rand_points
        print(f"{self_card.name} 技能10触发，随机加 {rand_points} 点，现在 {self_card.points}")


# -------------------- 通用技能 --------------------

class SkillDestroyEnemy(Skill):
    """消灭敌方场上一张牌"""
    targets_required = 1
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        target_card = targets[0]
        for player in board.players:
            if target_card in board.get_player_board(player):
                board.get_player_board(player).remove(target_card)
                print(f"{owner.name} 消灭了 {player.name} 的 {target_card.name}")
                break


class SkillDrawCard(Skill):
    """玩家抽一张牌（可指定目标玩家抽）"""
    targets_required = 0
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        if not targets:
            owner.draw_card_random()
            print(f"{owner.name} 抽到一张牌")
        else:
            for target_player in targets:
                if target_player.hand:
                    card = target_player.hand.pop(0)
                    owner.hand.append(card)
                    print(f"{owner.name} 从 {target_player.name} 抽到 {card.name}")
