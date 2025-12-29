import json
import pathlib


class RelicChecker:
    UNIQUENESS_IDS: set[str] = {
        "1000",
        "1010",
        "1020",
        "1030",
        "1040",
        "1050",
        "1060",
        "1070",
        "1080",
        "1090",
        "1100",
        "1110",
        "1120",
        "1130",
        "1140",
        "1150",
        "1160",
        "1170",
        "1180",
        "1190",
        "1200",
        "1210",
        "1220",
        "1230",
        "1240",
        "1250",
        "1260",
        "1270",
        "1300",
        "1310",
        "1400",
        "1410",
        "1420",
        "1430",
        "1440",
        "1450",
        "1460",
        "1470",
        "1480",
        "1490",
        "1500",
        "1510",
        "1520",
        "1600",
        "1610",
        "1620",
        "1630",
        "1640",
        "1650",
        "1660",
        "1670",
        "1680",
        "1690",
        "1700",
        "1710",
        "1720",
        "1730",
        "1740",
        "1750",
        "1800",
        "1820",
        "1830",
        "1850",
        "1860",
        "1870",
        "1880",
        "1890",
        "1900",
        "1920",
        "2000",
        "2001",
        "2010",
        "2011",
        "2020",
        "2021",
        "2030",
        "2031",
        "2040",
        "2041",
        "2050",
        "2051",
        "2060",
        "2061",
        "2070",
        "2071",
        "2080",
        "2100",
        "10000",
        "10001",
        "10002",
        "11000",
        "11001",
        "11002",
        "11003",
        "11004",
        "12000",
        "12001",
        "12002",
        "12003",
        "12004",
        "12005",
        "12006",
        "12007",
        "13001",
        "13002",
        "14000",
        "14001",
        "14002",
        "15000",
        "15002",
        "16001",
        "16002",
        "17001",
        "17002",
        "18000",
        "18002",
        "19000",
        "19001",
        "19050",
        "19051",
    }
    ILLEGAL_RELIC_IDS: set[str] = {
        "20000",
        "20001",
        "20002",
        "20003",
        "20004",
        "20005",
        "20006",
        "20007",
        "20008",
        "20009",
        "20010",
        "20011",
        "20012",
        "20013",
        "20014",
        "20015",
        "20016",
        "20017",
        "20018",
        "20019",
        "20020",
        "20021",
        "20022",
        "20023",
        "20024",
        "20025",
        "20026",
        "20027",
        "20028",
        "20029",
        "20030",
        "20031",
        "20032",
        "20033",
        "20034",
        "20035",
        "30000",
        "30001",
        "30002",
        "30003",
        "30004",
        "30005",
        "30006",
        "30007",
        "30008",
        "30009",
        "30010",
        "30011",
        "30012",
        "30013",
        "30014",
        "30015",
        "30016",
        "30017",
        "30018",
        "30019",
        "30020",
        "30021",
        "30022",
        "30023",
        "30024",
        "30025",
        "30026",
        "30027",
        "30028",
        "30029",
        "30030",
        "30031",
        "30032",
        "30033",
        "30034",
        "30035",
    }
    RELIC_RANGE: tuple[int, int] = (100, 2013322)

    def __init__(self, ga_relic, json_dir="Resources/Json"):
        self.json_dir = pathlib.Path(json_dir)
        self.ga_relic = ga_relic
        self.items_json = self._load_json("items.json")
        self.effects_json = self._load_json("effects.json")
        self.relic_effects_pool = self._load_json("relic_eff_pool.json")
        self.relic_eff_table_map = self._load_json("relic_eff_table_map.json")

    def _load_json(self, filename):
        with open(self.json_dir / filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def _check_relic_effects_in_pool(self, relic_id: str, effects: list[str]):
        """
        Check that all relic effects are in the relic effects pool.
        """
        # Check each effect is in pool
        relic_pool_mapped = self.relic_eff_table_map.get(relic_id, {})
        pools = [
            relic_pool_mapped.get("attachEffectTableId_1", "-1"),
            relic_pool_mapped.get("attachEffectTableId_2", "-1"),
            relic_pool_mapped.get("attachEffectTableId_3", "-1"),
            relic_pool_mapped.get("attachEffectTableId_curse1", "-1"),
            relic_pool_mapped.get("attachEffectTableId_curse2", "-1"),
            relic_pool_mapped.get("attachEffectTableId_curse3", "-1"),
        ]
        possible_sequences = [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0],
                              [2, 0, 1], [2, 1, 0]]
        test_results = []
        for seq in possible_sequences:
            cur_effects = [effects[i] for i in seq]
            cur_effects.extend([effects[i+3] for i in seq])
            test_result = []
            for idx, eff in enumerate(cur_effects):
                if pools[idx] == "-1":
                    if eff != "4294967295":  # 4294967295 means Empty
                        test_result.append(False)
                    else:
                        test_result.append(True)
                else:
                    if eff not in self.relic_effects_pool[pools[idx]]:
                        test_result.append(False)
                    else:
                        test_result.append(True)
                if idx == 5:
                    test_results.append(all(test_result))
                    test_result = []
        if not any(test_results):
            print("pause")
        return any(test_results)

    def _is_illegal(self, relic_id: str, effects: list[str]):

        # Rule 1
        if relic_id in self.ILLEGAL_RELIC_IDS:
            return True
        # Rule 2
        if not self._check_relic_effects_in_pool(relic_id, effects):
            return True

        if int(relic_id) not in range(self.RELIC_RANGE[0],
                                      self.RELIC_RANGE[1]+1):
            return True
        if relic_id in self.UNIQUENESS_IDS:
            # Exclude Unique Relic apply general rules
            return False
        else:
            used_ids = set()
            used_base_names = {}
            for idx, eff in enumerate(effects, start=1):
                # Treat unknown effects as empty
                if eff in ("0", "-1", "4294967295"):
                    continue

                eff_key = eff

                # Lookup in main effects DB
                eff_name = self.effects_json.get(
                    eff_key, {}).get(
                        "name", f"Unknown({eff})")

                # Rule 3 — duplicate ID
                if eff in used_ids:
                    return True
                used_ids.add(eff)

                # Rule 4 — conflicting tiers
                base_name = eff_name.rsplit(" +", 1)[0] \
                    if " +" in eff_name else eff_name
                if base_name in used_base_names:
                    return True

                used_base_names[base_name] = eff_name
            return False

    def get_illegal_relics(self):
        illegal_relics = []
        relic_group_by_id = {}
        for relic in self.ga_relic:
            ga, relic_id, e1, e2, e3, e4, e5, e6, offset, size = relic
            real_id = relic_id - 2147483648
            if str(real_id) not in relic_group_by_id.keys():
                relic_group_by_id[str(real_id)] = []
            relic_group_by_id[str(real_id)].append(relic)
            if self._is_illegal(str(real_id), [str(e1), str(e2), str(e3),
                                               str(e4), str(e5), str(e6)]):
                illegal_relics.append(ga)

        for real_id, relics in relic_group_by_id.items():
            if real_id in self.UNIQUENESS_IDS:
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
        return illegal_relics
