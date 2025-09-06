# game/ui_manager.py

class UIManager:
    """
    UI 管理类，负责处理玩家的交互操作，
    包括选择手牌、选择技能目标、确认操作等。
    """

    def __init__(self, players, board):
        self.players = players
        self.board = board

    def select_card_from_hand(self, player):
        """
        玩家从手牌中选择一张牌出牌
        :param player: 当前玩家对象
        :return: 选中的 Card 对象
        """
        # TODO: 替换成真实点击事件逻辑
        if not player.hand:
            return None
        # 临时示意：选择第一张手牌
        return player.hand[0]

    def select_target_card(self, player, skill):
        """
        玩家选择技能作用的单张目标牌
        :param player: 当前玩家对象（出牌者）
        :param skill: 当前技能对象
        :return: Card 对象
        """
        # TODO: 替换成 UI 点击事件逻辑
        # 示例：遍历所有玩家的战场牌，返回第一个可以选择的牌
        for p in self.players:
            if p == player:
                continue  # 跳过自己，如果技能不能作用于自己
            if p.board_cards:
                return p.board_cards[0]
        return None

    def select_target_cards(self, player, skill):
        """
        玩家选择技能作用的多张目标牌
        :param player: 当前玩家对象
        :param skill: 当前技能对象
        :return: Card 列表
        """
        # TODO: 替换成 UI 多选事件逻辑
        targets = []
        for p in self.players:
            if p == player:
                continue
            targets.extend(p.board_cards)
        return targets

    def confirm_action(self, player, action_desc):
        """
        弹出确认操作提示，例如是否打出牌、是否发动技能
        :param player: 当前玩家
        :param action_desc: 描述信息
        :return: True / False
        """
        # TODO: 替换成真实点击按钮逻辑
        print(f"{player.name} 确认操作: {action_desc}")
        return True  # 临时总是返回确认

    # 示例主流程函数
    def player_turn(self, player):
        """
        玩家回合主流程
        """
        while True:
            card = self.select_card_from_hand(player)
            if not card:
                print(f"{player.name} 没有手牌可出")
                break

            # 确认打出
            if not self.confirm_action(player, f"是否打出 {card.name}"):
                break

            # 技能前收集目标
            targets = []
            target = None
            for skill in card.skills:
                if getattr(skill, "needs_target", False):
                    # 单目标
                    target = self.select_target_card(player, skill)
                elif getattr(skill, "needs_targets", False):
                    # 多目标
                    targets = self.select_target_cards(player, skill)

            # 出牌并触发技能
            card.play(owner=player, board=self.board, target_card=target, targets=targets)

            # TODO: 根据规则判断是否继续出牌或结束回合
            if not self.confirm_action(player, "是否继续出牌？"):
                break
