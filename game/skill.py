# game/skill.py
from abc import ABC, abstractmethod

from abc import ABC, abstractmethod

class Skill(ABC):
    """
    技能抽象基类，所有技能必须继承此类并实现 apply 方法。

    apply 方法统一定义了可能会用到的参数，每个具体技能根据需求使用对应参数，
    用不到的参数默认为 None。
    """

    @abstractmethod
    def apply(self, owner=None, board=None, self_card=None, target_card=None, targets=None):
        """
        技能生效逻辑（必须由子类实现）

        :param owner: Skill 所属玩家对象（出牌的玩家）
        :param board: 游戏 Board 对象，可用于查询或修改战场、孤立区等
        :param self_card: 当前触发技能的卡牌对象（可能影响自身点数或效果）
        :param target_card: 目标卡牌对象（技能作用于单张指定卡牌时使用）
        :param targets: 目标卡牌对象列表（技能作用于多张卡牌时使用）
        """
        pass


# -------------------- 示例技能 --------------------
class Skill_1(Skill):
    """
    本牌上场时，根据己方场上牌数给自己加分
    """
    def apply(self, owner, board, self_card=None):
        """
        :param owner: 技能所属玩家
        :param board: 游戏 Board 对象
        :param targets: 可忽略，这里不需要
        :param self_card: 当前触发技能的牌对象
        """
        if self_card is None:
            return  # 没有指定触发的牌

        # 获取自己战场上的牌数量（包括刚打出的牌）
        cards_on_board = board.get_player_board(owner)
        num_cards = len(cards_on_board)

        # 给自己加点
        self_card.points += num_cards
        print(f"{self_card.name} 被触发，场上有 {num_cards} 张牌，点数增加到 {self_card.points}")

class Skill_2(Skill):
    """
    如果自己战场上只有这张牌，则给这张牌加5点
    """
    def apply(self, owner, board, self_card=None, target_card=None):
        """
        :param owner: 技能所属玩家
        :param board: 游戏 Board 对象
        :param self_card: 当前触发技能的牌对象
        """
        if self_card is None:
            return  # 安全检查

        # 获取自己战场上的牌列表
        cards_on_board = board.get_player_board(owner)

        # 判断是否只有这张牌
        if len(cards_on_board) == 1 and cards_on_board[0] == self_card:
            self_card.points += 5
            print(f"{self_card.name} 技能触发：战场上只有它，点数增加到 {self_card.points}")


class Skill_3(Skill):
    """
    给场上指定的一张牌加2点
    """
    def apply(self, owner=None, board=None, target_card=None):
        """
        :param owner: 技能所属玩家（打出这张牌的玩家）
        :param board: 战场对象
        :param target_card: 技能作用的目标牌对象
        """
        if board is None or target_card is None:
            return  # 安全检查

        target_card.points += 2
        print(f"{target_card.name} 被 {owner.name} 的技能加2点，点数现在为 {target_card.points}")

class Skill_4(Skill):
    """
    如果上一小局玩家获胜，则该玩家得分增加固定分数
    """
    def __init__(self, points=3):
        self.points = points  # 想加的分数

    def apply(self, owner=None, board=None, **kwargs):
        """
        :param owner: 技能所属玩家
        :param board: 游戏 Board 对象（可选）
        """
        if owner is None:
            return

        # 使用 getattr 安全获取 prev_round_won 属性，默认为 False
        if getattr(owner, "prev_round_won", False):
            owner.score += self.points
            print(f"{owner.name} 上一小局获胜，技能触发，得分增加 {self.points} 分，总分 {owner.score}")


class Skill_5(Skill):
    """
    上一回合输的玩家得到 +3 分
    """
    def apply(self, owner=None, board=None, **kwargs):
        if board is None or owner is None:
            return

        # 遍历所有玩家
        for player in board.players:
            if not getattr(player, "prev_round_won", False):  # 上一回合没有获胜
                player.score += 3
                print(f"{player.name} 上一回合输了，技能触发 +3 分，当前分数 {player.score}")


class SkillDestroyEnemy(Skill):
    """
    消灭敌方场上一张牌
    """
    def apply(self, owner, board, targets=None):
        # 默认随机选一个敌方玩家
        enemies = [p for p in board.players if p != owner]
        if targets:
            enemies = targets  # 如果传入了目标玩家，则覆盖默认敌人
        for enemy in enemies:
            enemy_board = board.get_player_board(enemy)
            if enemy_board:
                destroyed = enemy_board.pop(0)  # 消灭最前面一张牌
                print(f"{owner.name} 消灭了 {enemy.name} 的 {destroyed.name}")

class SkillDrawCard(Skill):
    """
    玩家抽一张牌
    """
    def apply(self, owner, board, targets=None):
        # targets 可选，用于指定从谁那里抽牌（默认自己补牌）
        if not targets:
            # 假设 draw_card 是 Player 类的方法
            owner.draw_card_random()
            print(f"{owner.name} 抽到一张牌")
        else:
            for target_player in targets:
                # 从指定玩家抽牌，逻辑可自定义
                if target_player.hand:
                    card = target_player.hand.pop(0)
                    owner.hand.append(card)
                    print(f"{owner.name} 从 {target_player.name} 抽到 {card.name}")
