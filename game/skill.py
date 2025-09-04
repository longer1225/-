# game/skill.py
from abc import ABC, abstractmethod

class Skill(ABC):
    """
    技能抽象基类，所有技能必须继承此类并实现 apply 方法。
    
    每个技能通过 `targets_required` 声明自己需要的目标数量：
      - 0 表示不需要点击目标
      - 1 表示需要玩家点击一张牌
      - n 表示需要点击 n 个目标
    UI 层根据这个参数提示玩家点击并收集目标，再传给 apply。
    """

    targets_required = 0  # 默认技能不需要目标

    @abstractmethod
    def apply(self, owner=None, board=None, self_card=None, targets=None):
        """
        技能生效逻辑（必须由子类实现）

        :param owner: 技能所属玩家对象（出牌的玩家）
        :param board: 游戏 Board 对象，可用于查询或修改战场、孤立区等
        :param self_card: 当前触发技能的卡牌对象
        :param targets: 由 UI 层点击选择后传入的卡牌列表
        """
        pass


# -------------------- 示例技能 --------------------
class Skill_1(Skill):
    """
    本牌上场时，根据己方场上牌数给自己加分
    """
    targets_required = 0

    def apply(self, owner=None, board=None, self_card=None, targets=None):
        if self_card is None or owner is None or board is None:
            return

        cards_on_board = board.get_player_board(owner)
        num_cards = len(cards_on_board)

        self_card.points += num_cards
        print(f"{self_card.name} 技能触发，场上有 {num_cards} 张牌，点数增加到 {self_card.points}")


class Skill_2(Skill):
    """
    如果自己战场上只有这张牌，则给这张牌加5点
    """
    targets_required = 0

    def apply(self, owner=None, board=None, self_card=None, targets=None):
        if self_card is None or owner is None or board is None:
            return

        cards_on_board = board.get_player_board(owner)
        if len(cards_on_board) == 1 and cards_on_board[0] == self_card:
            self_card.points += 5
            print(f"{self_card.name} 技能触发：战场上只有它，点数增加到 {self_card.points}")


class Skill_3(Skill):
    """
    给场上指定的一张牌加2点
    """
    targets_required = 1  # 需要点击一张牌

    def apply(self, owner=None, board=None, self_card=None, targets=None):
        if not targets or len(targets) != 1:
            return
        target_card = targets[0]

        target_card.points += 2
        print(f"{target_card.name} 被 {owner.name} 的技能加2点，点数现在为 {target_card.points}")


class Skill_4(Skill):
    """
    如果上一小局玩家获胜，则该玩家得分增加固定分数
    """
    targets_required = 0

    def __init__(self, points=3):
        self.points = points

    def apply(self, owner=None, board=None, self_card=None, targets=None):
        if owner is None:
            return

        if getattr(owner, "prev_round_won", False):
            owner.score += self.points
            print(f"{owner.name} 上一小局获胜，技能触发，得分增加 {self.points} 分，总分 {owner.score}")


class Skill_5(Skill):
    """
    上一回合输的玩家得到 +3 分
    """
    targets_required = 0

    def apply(self, owner=None, board=None, self_card=None, targets=None):
        if board is None:
            return

        for player in board.players:
            if not getattr(player, "prev_round_won", False):
                player.score += 3
                print(f"{player.name} 上一回合输了，技能触发 +3 分，当前分数 {player.score}")

# game/skill.py

class Skill_6(Skill):
    """
    技能6：抽取一张牌到手牌区（一定能抽到，因为牌是无限的）
    """
    def apply(self, owner=None, board=None, **kwargs):
        if owner is None or board is None:
            return

        # 从 GameManager 抽一张牌（保证一定有牌）
        new_card = board.manager.draw_card_for_player(owner)
        owner.hand.append(new_card)
        print(f"{owner.name} 触发技能6：抽到 {new_card.name}，加入手牌区")

# game/skill.py
class Skill_7(Skill):
    """
    技能7：消灭敌方场上的一张指定牌
    """
    def apply(self, owner=None, board=None, target_card=None, **kwargs):
        """
        :param owner: 技能所属玩家
        :param board: 游戏 Board 对象
        :param target_card: 玩家通过点击选中的目标卡牌
        """
        if owner is None or board is None or target_card is None:
            return

        # 找到目标卡属于哪个玩家
        target_owner = None
        for player in board.players:
            if target_card in board.get_player_board(player):
                target_owner = player
                break

        if target_owner is None:
            print("目标卡不在场上，技能无效")
            return

        # 从该玩家的战场区移除目标牌
        board.get_player_board(target_owner).remove(target_card)
        print(f"{owner.name} 使用技能7，消灭了 {target_owner.name} 的 {target_card.name}")

# game/skill.py

class Skill_8(Skill):
    """
    技能8：打出这张牌之前，自己战场上每有一张8，这张牌的点数+3
    """
    def apply(self, owner=None, board=None, self_card=None, **kwargs):
        """
        :param owner: 技能所属玩家
        :param board: 游戏 Board 对象
        :param self_card: 当前触发技能的卡牌对象（打出的8）
        """
        if owner is None or board is None or self_card is None:
            return

        # 统计自己战场已有几张8（不包括当前打出的牌）
        cards_on_board = board.get_player_board(owner)
        count_8 = sum(1 for card in cards_on_board if card.name == "8" and card != self_card)


        # 增加当前牌的点数
        if count_8 > 0:
            self_card.points += 3 * count_8
            print(f"{self_card.name} 技能触发，己方战场已有 {count_8} 张8，点数增加到 {self_card.points}")

class Skill_9(Skill):
    """
    拼点技能：
    - 打出该牌时选择一个目标玩家
    - 双方各随机生成一个点数
    - 点数大的一方胜利，胜者随机抽一张牌，败者弃掉玩家选择的一张牌
    """
    def apply(self, owner=None, board=None, target_player=None, self_card=None, discard_choice=None, **kwargs):
        """
        :param owner: 出牌玩家
        :param board: 战场对象
        :param target_player: 被选择拼点的玩家
        :param self_card: 当前触发技能的牌
        :param discard_choice: 败者选择弃掉的牌对象，由 UI 点击传入
        """
        if owner is None or board is None or target_player is None:
            return  # 安全检查

        # 双方随机点数
        owner_point = random.randint(1, 6)
        target_point = random.randint(1, 6)
        print(f"{owner.name} 拼点 {owner_point} vs {target_player.name} 拼点 {target_point}")

        if owner_point > target_point:
            print(f"{owner.name} 获胜，抽一张牌")
            owner.draw_card_random()
            if discard_choice:
                target_player.hand.remove(discard_choice)
                print(f"{target_player.name} 弃掉 {discard_choice.name}")
        elif owner_point < target_point:
            print(f"{target_player.name} 获胜，抽一张牌")
            target_player.draw_card_random()
            if discard_choice:
                owner.hand.remove(discard_choice)
                print(f"{owner.name} 弃掉 {discard_choice.name}")
        else:
            print("拼点平局，无人行动")

class Skill_10(Skill):
    """
    出牌时给自己增加 1-6 的随机点数
    """
    def apply(self, owner=None, board=None, self_card=None, **kwargs):
        """
        :param owner: 出牌玩家
        :param board: 游戏 Board 对象
        :param self_card: 当前触发技能的牌对象
        """
        if owner is None or self_card is None:
            return

        import random
        rand_points = random.randint(1, 6)
        self_card.points += rand_points
        print(f"{self_card.name} 技能触发，随机加 {rand_points} 点，当前点数 {self_card.points}")


class SkillDestroyEnemy(Skill):
    """
    消灭敌方场上一张牌
    """
    targets_required = 1  # 必须点一张敌方牌

    def apply(self, owner=None, board=None, self_card=None, targets=None):
        if not targets or len(targets) != 1:
            return
        target_card = targets[0]

        # 找到这张牌在哪个玩家战场
        for player in board.players:
            player_board = board.get_player_board(player)
            if target_card in player_board:
                player_board.remove(target_card)
                print(f"{owner.name} 消灭了 {player.name} 的 {target_card.name}")
                break


class SkillDrawCard(Skill):
    """
    玩家抽一张牌（可指定目标玩家抽）
    """
    targets_required = 0  # 默认自己抽，不需要点

    def apply(self, owner=None, board=None, self_card=None, targets=None):
        if not targets:  # 没指定 → 默认自己抽
            owner.draw_card_random()
            print(f"{owner.name} 抽到一张牌")
        else:
            for target_player in targets:
                if target_player.hand:
                    card = target_player.hand.pop(0)
                    owner.hand.append(card)
                    print(f"{owner.name} 从 {target_player.name} 抽到 {card.name}")
