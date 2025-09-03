# game/skill.py
from abc import ABC, abstractmethod

class Skill(ABC):
    """
    技能抽象基类，所有技能继承该类并实现 apply 方法
    """
    @abstractmethod
    def apply(self, owner, board):
        """
        技能生效逻辑
        :param owner: 技能所属玩家对象
        :param board: 游戏 Board 对象，用于修改战场或孤立区
        """
        pass

# -------------------- 示例技能 --------------------

class SkillAddPoint(Skill):
    """
    已方场上每有一张牌就加一分
    """
    def apply(self, owner, board):
        # 示例逻辑：打印触发
        print(f"{owner.name} 的 SkillAddPoint 被触发")

class SkillDestroyEnemy(Skill):
    """
    消灭敌方场上一张牌
    """
    def apply(self, owner, board):
        # 示例逻辑：打印触发
        print(f"{owner.name} 的 SkillDestroyEnemy 被触发")

class SkillDrawCard(Skill):
    """
    玩家抽一张牌
    """
    def apply(self, owner, board):
        # 示例逻辑：打印触发
        print(f"{owner.name} 的 SkillDrawCard 被触发")
