from source_data_handler import SourceDataHandler


class RelicChecker:
    RELIC_RANGE: tuple[int, int] = (100, 2013322)
    RELIC_GROUPS: dict[str, tuple[int, int]] = {"store_102": (100, 199),
                                                "store_103": (200, 299),
                                                "unique_1": (1000, 2100),
                                                "unique_2": (10000, 19999),
                                                "illegal": (20000, 30035),
                                                "reward_0": (1000000, 1000999),
                                                "reward_1": (1001000, 1001999),
                                                "reward_2": (1002000, 1002999),
                                                "reward_3": (1003000, 1003999),
                                                "reward_4": (1004000, 1004999),
                                                "reward_5": (1005000, 1005999),
                                                "reward_6": (1006000, 1006999),
                                                "reward_7": (1007000, 1007999),
                                                "reward_8": (1008000, 1008999),
                                                "reward_9": (1009000, 1009999),
                                                "deep_102": (2000000, 2009999),
                                                "deep_103": (2010000, 2019999)
                                                }
    UNIQUENESS_IDS: set[int] = \
        set(i for i in range(RELIC_GROUPS['unique_1'][0],
                             RELIC_GROUPS['unique_1'][1] + 1)) |\
        set(i for i in range(RELIC_GROUPS['unique_2'][0],
                             RELIC_GROUPS['unique_2'][1] + 1))

    def __init__(self, ga_relic, data_source: SourceDataHandler):
        self.ga_relic = ga_relic
        self.data_source = data_source
        self.illegal_gas = []

    def _check_relic_effects_in_pool(self, relic_id: int, effects: list[int]):
        """
        Check that all relic effects are in the relic effects pool.
        """
        # Load relic effects pool data
        try:
            pools = self.data_source.get_relic_pools_seq(relic_id)
        except KeyError:
            return False
        # There are 6 effects: 3 normal effects and 3 curse effects
        # The first 3 are normal effects, the last 3 are curse effects
        # Each effect corresponds to a pool ID
        # If pool ID is -1, the effect must be empty (4294967295)
        # If pool ID is not -1, the effect must be in the pool
        # Try all possible sequences of effects
        # Because we don't know the original order of effects
        possible_sequences = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0],
                              [2, 0, 1], [2, 1, 0]]
        test_results = []
        for seq in possible_sequences:
            cur_effects = [effects[i] for i in seq]
            cur_effects.extend([effects[i+3] for i in seq])
            test_result = []
            for idx, eff in enumerate(cur_effects):
                if pools[idx] == -1:
                    if eff != 4294967295:  # 4294967295 means Empty
                        test_result.append(False)
                    else:
                        test_result.append(True)
                else:
                    if eff not in self.data_source.get_pool_effects(pools[idx]):
                        test_result.append(False)
                    else:
                        test_result.append(True)
                if idx == 5:
                    test_results.append(all(test_result))
                    test_result = []
            if test_results[-1]:
                return True
        return False

    def is_illegal(self, relic_id: int, effects: list[int]):

        # Rule 1
        if relic_id in range(self.RELIC_GROUPS['illegal'][0],
                             self.RELIC_GROUPS['illegal'][1] + 1):
            return True
        # Rule 2
        if not self._check_relic_effects_in_pool(relic_id, effects):
            return True

        if relic_id not in range(self.RELIC_RANGE[0],
                                 self.RELIC_RANGE[1]+1):
            return True
        else:
            # Rule: The compatibilityId (conflict ID) should not be duplicated.
            conflict_ids = []
            for effect_id in effects:
                # Skip empty effects
                if effect_id in [-1, 0, 4294967295]:
                    continue
                conflict_id = \
                    self.data_source.get_effect_conflict_id(effect_id)
                # conflict id -1 is allowed to be duplicated
                if conflict_id in conflict_ids and conflict_id != -1:
                    return True
                conflict_ids.append(conflict_id)
            # Rule: Effect order
            # Effects are sorted in ascending order by overrideEffectId.
            # If overrideEffectId values are identical,
            # compare the effect IDs themselves.
            # Sorting considers only the top three positive effects.
            # Curse effects are bound to their corresponding positive effects.
            sort_ids = []
            for effect_id in effects[:3]:
                # Skip empty effects
                if effect_id in [-1, 0, 4294967295]:
                    sort_ids.append(float('inf'))
                else:
                    sort_id = self.data_source.get_sort_id(effect_id)
                    sort_ids.append(sort_id)
            sort_tuple = zip(sort_ids, effects[:3])
            sorted_effects = sorted(sort_tuple, key=lambda x: (x[0], x[1]))
            for i in range(len(sorted_effects)):
                if sorted_effects[i][1] != effects[i]:
                    return True
            return False

    def sort_effects(self, effects: list[int]):
        sort_ids = []
        curse_map = {}
        for idx, effect_id in enumerate(effects[:3]):
            curse_map[effect_id] = effects[idx+3]
            # Skip empty effects
            if effect_id in [-1, 0, 4294967295]:
                sort_ids.append(float('inf'))
            else:
                sort_id = self.data_source.get_sort_id(effect_id)
                sort_ids.append(sort_id)
        sort_tuple = zip(sort_ids, effects)
        sorted_effects = sorted(sort_tuple, key=lambda x: (x[0], x[1]))
        sorted_effects = [effect for _, effect in sorted_effects]
        result = [effect for effect in sorted_effects]
        result.extend([curse_map[effect] for effect in sorted_effects])
        return result

    def set_illegal_relics(self):
        illegal_relics = []
        relic_group_by_id = {}
        for relic in self.ga_relic:
            ga, relic_id, e1, e2, e3, e4, e5, e6, offset, size = relic
            real_id = relic_id - 2147483648
            if str(real_id) not in relic_group_by_id.keys():
                relic_group_by_id[str(real_id)] = []
            relic_group_by_id[str(real_id)].append(relic)
            if self.is_illegal(real_id, [e1, e2, e3,
                                          e4, e5, e6]):
                illegal_relics.append(ga)

        for real_id, relics in relic_group_by_id.items():
            if int(real_id) in self.UNIQUENESS_IDS:
                if len(relics) > 1:
                    legal_found = False
                    for relic in relics:
                        (ga, relic_id,
                         e1, e2, e3, e4, e5, e6,
                         offset, size) = relic
                        if ga in illegal_relics:
                            continue
                        if not legal_found:
                            legal_found = True
                            continue
                        illegal_relics.append(ga)
        self.illegal_gas = illegal_relics

    @property
    def illegal_count(self):
        return len(self.illegal_gas)

    def append_illegal(self, ga):
        self.illegal_gas.append(ga)

    def remove_illegal(self, ga):
        self.illegal_gas.remove(ga)

    def find_id_range(self, relic_id: int):
        for group_name, group_range in self.RELIC_GROUPS.items():
            if relic_id in range(group_range[0], group_range[1] + 1):
                return group_name, group_range
        return None
