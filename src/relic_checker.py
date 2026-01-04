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
        self.curse_illegal_gas = []  # Track relics illegal due to missing curses

    def _check_relic_effects_in_pool(self, relic_id: int, effects: list[int],
                                      allow_empty_curses: bool = False):
        """
        Check that all relic effects are in the relic effects pool.

        Args:
            relic_id: The relic ID to check
            effects: List of 6 effect IDs [e1, e2, e3, curse1, curse2, curse3]
            allow_empty_curses: If True, allow empty curse slots even if pool requires curse
                               (used to check if only curse is missing vs wrong effects)
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
                is_curse_slot = idx >= 3
                if pools[idx] == -1:
                    if eff != 4294967295:  # 4294967295 means Empty
                        test_result.append(False)
                    else:
                        test_result.append(True)
                else:
                    # Allow empty curse slots if flag is set
                    if allow_empty_curses and is_curse_slot and eff in [-1, 0, 4294967295]:
                        test_result.append(True)
                    elif eff not in self.data_source.get_pool_effects(pools[idx]):
                        test_result.append(False)
                    else:
                        test_result.append(True)
                if idx == 5:
                    test_results.append(all(test_result))
                    test_result = []
            if test_results[-1]:
                return True
        return False

    def _effect_needs_curse(self, effect_id: int) -> bool:
        """Check if an effect REQUIRES a curse.

        An effect needs a curse if it ONLY exists in pool 2000000 (which is always
        paired with curse_pool 3000000) and not in pools 2100000 or 2200000
        (which have no curse requirement) or any regular pools.
        """
        return self.data_source.effect_needs_curse(effect_id)

    def is_curse_illegal(self, relic_id: int, effects: list[int]):
        """Check if a relic is illegal ONLY due to missing curses.

        Returns True if:
        - The relic ID is valid for the effects (ignoring curse requirements)
        - But NO sequence exists where all curses are properly filled

        This distinguishes between:
        - RED: Wrong relic ID for effects (effects not in pool)
        - PURPLE: Correct relic ID but missing required curses in ALL sequences
        """
        # Check if relic ID is in valid range
        if relic_id not in range(self.RELIC_RANGE[0], self.RELIC_RANGE[1]+1):
            return False

        # Check if in illegal range
        if relic_id in range(self.RELIC_GROUPS['illegal'][0],
                             self.RELIC_GROUPS['illegal'][1] + 1):
            return False

        # Check if effects are valid for this relic (allowing empty curses)
        # If effects aren't valid even with empty curses allowed, it's not curse-illegal
        if not self._check_relic_effects_in_pool(relic_id, effects, allow_empty_curses=True):
            return False

        # Effects are valid. Now check if there's ANY sequence that is FULLY valid
        # (including proper curses). If such a sequence exists, it's NOT curse-illegal.
        try:
            pools = self.data_source.get_relic_pools_seq(relic_id)
        except KeyError:
            return False

        # Count effect slots to determine if this is a multi-effect relic
        effect_slot_count = sum(1 for p in pools[:3] if p != -1)

        # Single-effect relics (1 slot) don't need curses at all
        # Only multi-effect relics (2+ slots) have curse requirements
        if effect_slot_count <= 1:
            return False  # Single-effect relics are never curse-illegal

        # For multi-effect relics, count how many effects need curses
        # Deep-only effects require curses when on multi-effect relics
        deep_only_effects = sum(1 for eff in effects[:3]
                                if self._effect_needs_curse(eff))
        curses_provided = sum(1 for c in effects[3:]
                              if c not in [-1, 0, 4294967295])

        # Quick check: if not enough curses for deep-only effects
        if deep_only_effects > curses_provided:
            return True  # Not enough curses for deep-only effects

        possible_sequences = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0],
                              [2, 0, 1], [2, 1, 0]]

        for seq in possible_sequences:
            cur_effects = [effects[i] for i in seq]
            cur_curses = [effects[i + 3] for i in seq]

            # Check if this sequence is FULLY valid (effects AND curses)
            sequence_fully_valid = True

            for idx in range(3):
                eff = cur_effects[idx]
                curse = cur_curses[idx]
                effect_pool = pools[idx]
                curse_pool = pools[idx + 3]

                # Check effect is in pool
                if effect_pool == -1:
                    if eff != 4294967295:
                        sequence_fully_valid = False
                        break
                else:
                    if eff not in self.data_source.get_pool_effects(effect_pool):
                        sequence_fully_valid = False
                        break

                # Check curse is valid
                # For multi-effect relics:
                # - If effect needs curse AND curse_pool == -1 -> wrong relic
                # - If effect needs curse AND curse_pool != -1 -> curse MUST be provided
                # - If effect doesn't need curse AND curse_pool != -1 -> curse is OPTIONAL
                # - If curse_pool == -1 -> curse must be empty
                effect_needs_curse = self._effect_needs_curse(eff)

                if effect_needs_curse:
                    # Effect requires a curse
                    if curse_pool == -1:
                        # Relic doesn't support curse in this slot - wrong relic
                        sequence_fully_valid = False
                        break
                    if curse in [-1, 0, 4294967295]:
                        # Missing required curse
                        sequence_fully_valid = False
                        break
                    if curse not in self.data_source.get_pool_effects(curse_pool):
                        # Curse not in correct pool
                        sequence_fully_valid = False
                        break
                elif curse_pool != -1:
                    # Effect doesn't need curse but slot supports one (optional)
                    # Curse can be empty or valid
                    if curse not in [-1, 0, 4294967295]:
                        if curse not in self.data_source.get_pool_effects(curse_pool):
                            # Curse provided but not in correct pool
                            sequence_fully_valid = False
                            break
                else:
                    # curse_pool == -1: no curse allowed
                    if curse not in [-1, 0, 4294967295]:
                        # Has curse when slot doesn't support it
                        sequence_fully_valid = False
                        break

            # If we found a fully valid sequence, the relic is NOT curse-illegal
            if sequence_fully_valid:
                return False

        # No fully valid sequence found, but effects are valid -> curse-illegal
        return True

    def is_illegal(self, relic_id: int, effects: list[int]):

        # Rule 1
        if relic_id in range(self.RELIC_GROUPS['illegal'][0],
                             self.RELIC_GROUPS['illegal'][1] + 1):
            return True

        if relic_id not in range(self.RELIC_RANGE[0],
                                 self.RELIC_RANGE[1]+1):
            return True
        else:
            # Rule: Deep-only effects must have curses
            # Effects that only exist in deep relic pools require curses
            # when used on multi-effect relics
            if self.is_curse_illegal(relic_id, effects):
                return True

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
        """Sort effects by their sort ID, keeping curses paired with their primary effects.

        Effects structure: [effect1, effect2, effect3, curse1, curse2, curse3]
        After sorting, curse at position i always corresponds to effect at position i.
        """
        # Build list of (sort_id, effect_id, curse_id) tuples
        effect_curse_pairs = []
        curses = effects[3:]
        curse_tuples = []
        for idx in range(3):
            curse_id = curses[idx]
            if curse_id in [-1, 0, 4294967295]:
                sort_id = float('inf')  # Empty curses go last
            else:
                sort_id = self.data_source.get_sort_id(curse_id)
            curse_tuples.append((sort_id, curse_id))
        curse_tuples = sorted(curse_tuples, key=lambda x: (x[0], x[1]))
        curses = [pair[1] for pair in curse_tuples]

        for idx in range(3):
            effect_id = effects[idx]
            curse_id = 4294967295
            if self.data_source.effect_needs_curse(effect_id):
                curse_id = curses.pop(0)
            else:
                curse_id = curses.pop()

            # Get sort ID for the primary effect
            if effect_id in [-1, 0, 4294967295]:
                sort_id = float('inf')  # Empty effects go last
            else:
                sort_id = self.data_source.get_sort_id(effect_id)

            effect_curse_pairs.append((sort_id, effect_id, curse_id))

        # Sort by (sort_id, effect_id) - effect_id as tiebreaker
        sorted_pairs = sorted(effect_curse_pairs, key=lambda x: (x[0], x[1]))

        # Build result: sorted effects followed by their corresponding curses
        result = [pair[1] for pair in sorted_pairs]  # effects
        result.extend([pair[2] for pair in sorted_pairs])  # curses
        return result

    def set_illegal_relics(self):
        illegal_relics = []
        curse_illegal_relics = []
        relic_group_by_id = {}
        for relic in self.ga_relic:
            ga, relic_id, e1, e2, e3, e4, e5, e6, offset, size = relic
            real_id = relic_id - 2147483648
            if str(real_id) not in relic_group_by_id.keys():
                relic_group_by_id[str(real_id)] = []
            relic_group_by_id[str(real_id)].append(relic)
            effects = [e1, e2, e3, e4, e5, e6]
            if self.is_illegal(real_id, effects):
                illegal_relics.append(ga)
                # Check if it's specifically curse-illegal
                if self.is_curse_illegal(real_id, effects):
                    curse_illegal_relics.append(ga)

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
        self.curse_illegal_gas = curse_illegal_relics

    @property
    def illegal_count(self):
        return len(self.illegal_gas)

    def append_illegal(self, ga, is_curse_illegal=False):
        self.illegal_gas.append(ga)
        if is_curse_illegal:
            self.curse_illegal_gas.append(ga)

    def remove_illegal(self, ga):
        if ga in self.illegal_gas:
            self.illegal_gas.remove(ga)
        if ga in self.curse_illegal_gas:
            self.curse_illegal_gas.remove(ga)

    def find_id_range(self, relic_id: int):
        for group_name, group_range in self.RELIC_GROUPS.items():
            if relic_id in range(group_range[0], group_range[1] + 1):
                return group_name, group_range
        return None
