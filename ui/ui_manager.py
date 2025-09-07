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
        玩家从手牌中选择一张牌出牌（命令行交互）
        :param player: 当前玩家对象
        :return: 选中的 Card 对象
        """
        if not player.hand:
            print("没有手牌可选！")
            return None
        print(f"{player.name} 的手牌：")
        for idx, card in enumerate(player.hand):
            print(f"  [{idx}] {card.name} (点数: {getattr(card, 'points', '?')})")
        while True:
            try:
                choice = int(input("请选择要出的牌编号："))
                if 0 <= choice < len(player.hand):
                    return player.hand[choice]
                else:
                    print("输入超出范围，请重新输入。")
            except ValueError:
                print("请输入有效数字。")

    def select_target_card(self, player, skill):
        """
        玩家选择技能作用的单张目标牌（命令行交互）
        :param player: 当前玩家对象（出牌者）
        :param skill: 当前技能对象
        :return: Card 对象
        """
        candidates = []
        for p in self.players:
            if p == player:
                continue
            for card in p.board_cards:
                candidates.append((p, card))
        if not candidates:
            print("没有可选目标牌！")
            return None
        print("可选目标牌：")
        for idx, (p, card) in enumerate(candidates):
            print(f"  [{idx}] {p.name} 的 {card.name} (点数: {getattr(card, 'points', '?')})")
        while True:
            try:
                choice = int(input("请选择目标牌编号："))
                if 0 <= choice < len(candidates):
                    return candidates[choice][1]
                else:
                    print("输入超出范围，请重新输入。")
            except ValueError:
                print("请输入有效数字。")

    def select_target_cards(self, player, skill):
        """
        玩家选择技能作用的多张目标牌（命令行交互）
        :param player: 当前玩家对象
        :param skill: 当前技能对象
        :return: Card 列表
        """
        candidates = []
        for p in self.players:
            if p == player:
                continue
            for card in p.board_cards:
                candidates.append((p, card))
        if not candidates:
            print("没有可选目标牌！")
            return []
        print("可选目标牌（用逗号分隔编号，多选）：")
        for idx, (p, card) in enumerate(candidates):
            print(f"  [{idx}] {p.name} 的 {card.name} (点数: {getattr(card, 'points', '?')})")
        while True:
            try:
                choices = input("请选择目标牌编号（如0,2,3）：")
                idxs = [int(x) for x in choices.split(',') if x.strip().isdigit()]
                if all(0 <= i < len(candidates) for i in idxs):
                    return [candidates[i][1] for i in idxs]
                else:
                    print("输入有误，请重新输入。")
            except Exception:
                print("请输入有效编号，用逗号分隔。")

    def confirm_action(self, player, action_desc):
        """
        弹出确认操作提示，例如是否打出牌、是否发动技能（命令行交互）
        :param player: 当前玩家
        :param action_desc: 描述信息
        :return: True / False
        """
        while True:
            resp = input(f"{player.name}，{action_desc} (y/n)：").strip().lower()
            if resp in ("y", "yes"): return True
            if resp in ("n", "no"): return False
            print("请输入 y 或 n。")

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
