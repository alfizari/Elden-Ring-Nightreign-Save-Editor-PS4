import pandas as pd
import pathlib
from typing import Optional
import locale
import sys
import os


COLOR_MAP = ["Red", "Blue", "Yellow", "Green", "White"]
LANGUAGE_MAP = {
    "ar_AE": "العربية (الإمارات)",
    "de_DE": "Deutsch",
    "en_US": "English",
    "es_AR": "Español (Argentina)",
    "es_ES": "Español (España)",
    "fr_FR": "Français",
    "it_IT": "Italiano",
    "ja_JP": "日本語",
    "ko_KR": "한국어",
    "pl_PL": "Polski",
    "pt_BR": "Português (Brasil)",
    "ru_RU": "Русский",
    "th_TH": "ไทย",
    "zh_CN": "简体中文",
    "zh_TW": "繁體中文 (台灣)"
}
# Character names for vessel assignment
CHARACTER_NAME_ID = [100000, 100030, 100050, 100010, 100040, 100090,
                     100070, 100060, 110000, 110010]
CHARACTER_NAMES = ['Wylder', 'Guardian', 'Ironeye', 'Duchess', 'Raider',
                   'Revenant', 'Recluse', 'Executor', 'Scholar', 'Undertaker', 'All']


def get_system_language():
    lang = None

    try:
        lang, _ = locale.getdefaultlocale()
    except Exception:
        return "en_US"

    if lang:
        normalized = locale.normalize(lang)
        clean_lang = normalized.split('.')[0]
        clean_lang = clean_lang.replace('-', '_')
        if clean_lang in LANGUAGE_MAP:
            return clean_lang
        else:
            return "en_US"
    return "en_US"


def df_filter_zero_chanceWeight(effects: pd.DataFrame) -> pd.DataFrame:
    """
    Filter effects DataFrame to include only those with non-zero FINAL chanceWeight.
    chanceWeight_dlc explains from Smithbox(unpacking tool):
    The DLC new Weighting to apply during the roll.
    -1 will use base roll weight(chanceWeight).

    Args:
        effects (pd.DataFrame): DataFrame import from AttachEffectTableParam.csv .\n
            Can be filtered before calling this function,\n
            but must have 'chanceWeight' and 'chanceWeight_dlc' columns.

    Returns:
        DataFrame:
            Filtered DataFrame with effects that have non-zero chanceWeight
    """
    _effs = effects.copy()
    _effs = _effs[(_effs["chanceWeight_dlc"] > 0) |
                  ((_effs["chanceWeight"] != 0) & (_effs["chanceWeight_dlc"] == -1))]
    return _effs


class SourceDataHandler:
    WORKING_DIR = pathlib.Path(__file__).parent.resolve()
    PARAM_DIR = pathlib.Path(WORKING_DIR / "Resources/Param")
    TEXT_DIR = pathlib.Path(WORKING_DIR / "Resources/Text")
    RELIC_TEXT_FILE_NAME = ["AntiqueName.fmg.xml", "AntiqueName_dlc01.fmg.xml"]
    EFFECT_NAME_FILE_NAMES = [
        "AttachEffectName.fmg.xml",
        "AttachEffectName_dlc01.fmg.xml",
    ]
    NPC_NAME_FILE_NAMES = [
        "NpcName.fmg.xml",
        "NpcName_dlc01.fmg.xml",
    ]
    GOODS_NAME_FILE_NAMES = [
        "GoodsName.fmg.xml",
        "GoodsName_dlc01.fmg.xml",
    ]

    def __init__(self, language: str = "en_US"):
        self.effect_params = \
            pd.read_csv(self.PARAM_DIR / "AttachEffectParam.csv")
        self.effect_params: pd.DataFrame = self.effect_params[
            ["ID", "compatibilityId", "attachTextId", "overrideEffectId"]
        ]
        self.effect_params.set_index("ID", inplace=True)

        self.effect_table = \
            pd.read_csv(self.PARAM_DIR / "AttachEffectTableParam.csv")
        self.effect_table: pd.DataFrame = \
            self.effect_table[["ID", "attachEffectId", "chanceWeight", "chanceWeight_dlc"]]

        self.relic_table = \
            pd.read_csv(self.PARAM_DIR / "EquipParamAntique.csv")
        self.relic_table: pd.DataFrame = self.relic_table[
            [
                "ID",
                "relicColor",
                "attachEffectTableId_1",
                "attachEffectTableId_2",
                "attachEffectTableId_3",
                "attachEffectTableId_curse1",
                "attachEffectTableId_curse2",
                "attachEffectTableId_curse3",
            ]
        ]
        self.relic_table.set_index("ID", inplace=True)

        self.antique_stand_param = \
            pd.read_csv(self.PARAM_DIR / "AntiqueStandParam.csv")
        self.antique_stand_param: pd.DataFrame = self.antique_stand_param

        self.relic_name: Optional[pd.DataFrame] = None
        self.effect_name: Optional[pd.DataFrame] = None
        self.npc_name: Optional[pd.DataFrame] = None
        # Track which relic IDs are from 1.02 patch (Scene relics)
        self._scene_relic_ids: set = set()
        self.vessel_names: Optional[pd.DataFrame] = None
        self._load_text(language)

    def _load_text(self, language: str = "en_US"):
        support_languages = LANGUAGE_MAP.keys()
        _lng = language
        if language not in support_languages:
            _lng = "en_US"
        # Deal with Relic text
        # Read all Relic xml from language subfolder
        # Track which IDs come from _dlc01 file (1.02 patch / Scene relics)
        _relic_names: Optional[pd.DataFrame] = None
        self._scene_relic_ids = set()
        for file_name in SourceDataHandler.RELIC_TEXT_FILE_NAME:
            _df = pd.read_xml(
                SourceDataHandler.TEXT_DIR / _lng / file_name,
                xpath="/fmg/entries/text"
            )
            # Track IDs from dlc01 file as Scene relics (1.02 patch)
            if "_dlc01" in file_name:
                valid_ids = _df[_df['text'] != '%null%']['id'].tolist()
                self._scene_relic_ids.update(valid_ids)
            if _relic_names is None:
                _relic_names = _df
            else:
                _relic_names = pd.concat([_relic_names, _df])

        # Deal with Effect text
        # Read all Effect xml from language subfolder
        _effect_names: Optional[pd.DataFrame] = None
        for file_name in SourceDataHandler.EFFECT_NAME_FILE_NAMES:
            _df = pd.read_xml(
                SourceDataHandler.TEXT_DIR / _lng / file_name,
                xpath="/fmg/entries/text"
            )
            if _effect_names is None:
                _effect_names = _df
            else:
                _effect_names = pd.concat([_effect_names, _df])

        # Deal with NPC text
        # Read all NPC xml from language subfolder
        _npc_names: Optional[pd.DataFrame] = None
        for file_name in SourceDataHandler.NPC_NAME_FILE_NAMES:
            _df = pd.read_xml(
                SourceDataHandler.TEXT_DIR / _lng / file_name,
                xpath="/fmg/entries/text"
            )
            if _npc_names is None:
                _npc_names = _df
            else:
                _npc_names = pd.concat([_npc_names, _df])

        global CHARACTER_NAMES
        CHARACTER_NAMES.clear()
        for id in CHARACTER_NAME_ID:
            _name = _npc_names[_npc_names["id"] == id]["text"].to_list()[0]
            CHARACTER_NAMES.append(_name)

        # Deal with Goods Names
        # Read all Goods xml from language subfolder
        _goods_names: Optional[pd.DataFrame] = None
        for file_name in SourceDataHandler.GOODS_NAME_FILE_NAMES:
            _df = pd.read_xml(
                SourceDataHandler.TEXT_DIR / _lng / file_name,
                xpath="/fmg/entries/text"
            )
            if _goods_names is None:
                _goods_names = _df
            else:
                _goods_names = pd.concat([_goods_names, _df])

        self.vessel_names = _goods_names[(9600 <= _goods_names["id"]) &
                                         (_goods_names["id"] <= 9956) &
                                         (_goods_names["text"] != "%null%")]
        self.npc_name = _npc_names
        self.relic_name = _relic_names
        self.effect_name = _effect_names

    def reload_text(self, language: str = "en_US"):
        try:
            self._load_text(language=language)
            return True
        except FileNotFoundError:
            self._load_text()
            return False
        except KeyError:
            self._load_text()
            return False

    def get_support_languages_name(self):
        return LANGUAGE_MAP.values()

    def get_support_languages_code(self):
        return LANGUAGE_MAP.keys()

    def get_support_languages(self):
        return LANGUAGE_MAP

    def get_relic_origin_structure(self):
        if self.relic_name is None:
            self._load_text()
        _copy_df = self.relic_name.copy()
        _copy_df.set_index("id", inplace=True)
        _copy_df.rename(columns={"text": "name"}, inplace=True)
        _result = {}
        for index, row in self.relic_table.iterrows():
            try:
                _name_matches = \
                    _copy_df[_copy_df.index == index]["name"].values
                _color_matches = \
                    self.relic_table[self.relic_table.index == index][
                        "relicColor"].values
                first_name_val = \
                    _name_matches[0] if len(_name_matches) > 0 else "Unset"
                first_color_val = COLOR_MAP[int(_color_matches[0])] if len(_color_matches) > 0 else "Red"
                _result[str(index)] = {
                    "name": str(first_name_val),
                    "color": first_color_val,
                }
            except KeyError:
                _result[str(index)] = {"name": "Unset", "color": "Red"}
        return _result

    def get_relic_datas(self):
        if self.relic_name is None:
            self._load_text()
        _name_map = self.relic_name.copy()
        _name_map.reset_index(inplace=True, drop=True)
        _name_map.rename(columns={"text": "name"}, inplace=True)
        _result = self.relic_table.copy()
        _result.reset_index(inplace=True)
        _result = pd.merge(
            _result,
            _name_map,
            how="left",
            left_on="ID",
            right_on="id",
        )
        _result.drop(columns=["id"], inplace=True)
        _result.set_index("ID", inplace=True)
        return _result

    def cvrt_filtered_relic_origin_structure(self,
                                             relic_dataframe: pd.DataFrame):
        if self.relic_name is None:
            self._load_text()
        _copy_df = self.relic_name.copy()
        _copy_df.set_index("id", inplace=True)
        _copy_df.rename(columns={"text": "name"}, inplace=True)
        _result = {}
        for index, row in relic_dataframe.iterrows():
            try:
                _name_matches = \
                    _copy_df[_copy_df.index == index]["name"].values
                _color_matches = \
                    relic_dataframe[relic_dataframe.index == index][
                        "relicColor"].values
                first_name_val = \
                    _name_matches[0] if len(_name_matches) > 0 else "Unset"
                first_color_val = COLOR_MAP[int(_color_matches[0])] if len(_color_matches) > 0 else "Red"
                _result[str(index)] = {
                    "name": str(first_name_val),
                    "color": first_color_val,
                }
            except KeyError:
                _result[str(index)] = {"name": "Unset", "color": "Red"}
        return _result

    def get_effect_datas(self):
        if self.effect_name is None:
            self._load_text()
        _name_map = self.effect_name.copy()
        _name_map.reset_index(inplace=True, drop=True)
        _name_map.rename(columns={"text": "name"}, inplace=True)
        _result = self.effect_params.copy()
        _result.reset_index(inplace=True)
        _result = pd.merge(
            _result,
            _name_map,
            how="left",
            left_on="attachTextId",
            right_on="id",
        )
        _result.drop(columns=["id"], inplace=True)
        _result.set_index("ID", inplace=True)
        _result.fillna({"name": "Unknown"}, inplace=True)
        return _result

    def get_effect_origin_structure(self):
        if self.effect_name is None:
            self._load_text()
        _copy_df = self.effect_name.copy()
        _copy_df.set_index("id", inplace=True)
        _reslut = {"4294967295": {"name": "Empty"}}
        for index, row in self.effect_params.iterrows():
            try:
                _attachTextId = self.effect_params.loc[index, "attachTextId"]
                matches = \
                    _copy_df[_copy_df.index == _attachTextId]["text"].values
                first_val = matches[0] if len(matches) > 0 else "Unknown"
                _reslut[str(index)] = {"name": str(first_val)}
            except KeyError:
                _reslut[str(index)] = {"name": "Unknown"}
        return _reslut

    def cvrt_filtered_effect_origin_structure(self,
                                              effect_dataframe: pd.DataFrame):
        if self.effect_name is None:
            self._load_text()
        _copy_df = self.effect_name.copy()
        _copy_df.set_index("id", inplace=True)
        _reslut = {}
        for index, row in effect_dataframe.iterrows():
            try:
                _attachTextId = effect_dataframe.loc[index, "attachTextId"]
                matches = \
                    _copy_df[_copy_df.index == _attachTextId]["text"].values
                first_val = matches[0] if len(matches) > 0 else "Unknown"
                _reslut[str(index)] = {"name": str(first_val)}
            except KeyError:
                _reslut[str(index)] = {"name": "Unknown"}
        if len(_reslut) == 0:
            _reslut = {"4294967295": {"name": "Empty"}}
        return _reslut

    def get_relic_pools_seq(self, relic_id: int):
        _pool_ids = self.relic_table.loc[relic_id,
                                         ["attachEffectTableId_1",
                                          "attachEffectTableId_2",
                                          "attachEffectTableId_3",
                                          "attachEffectTableId_curse1",
                                          "attachEffectTableId_curse2",
                                          "attachEffectTableId_curse3"]]
        return _pool_ids.values.tolist()

    def is_scene_relic(self, relic_id: int) -> bool:
        """Check if a relic is a Scene relic (added in patch 1.02).

        Scene relics have different effect pools than original relics,
        which is why certain effects can only be found on Scene relics
        and vice versa.

        Returns:
            True if the relic is a Scene relic (1.02+), False otherwise
        """
        return relic_id in self._scene_relic_ids

    def get_relic_type_info(self, relic_id: int) -> tuple:
        """Get relic type information for display purposes.

        Returns:
            Tuple of (type_name, description, color_hex)
            - type_name: "Scene" or "Original"
            - description: Brief explanation of what this means
            - color_hex: Color for display
        """
        if self.is_scene_relic(relic_id):
            return (
                "Scene Relic (1.02+)",
                "Has unique effect pools not found on original relics",
                "#9966CC"  # Purple for Scene relics
            )
        else:
            return (
                "Original Relic",
                "Has effect pools from base game release",
                "#666666"  # Gray for original relics
            )

    def get_effect_conflict_id(self, effect_id: int):
        try:
            if effect_id == -1 or effect_id == 4294967295:
                return -1
            _conflict_id = self.effect_params.loc[effect_id, "compatibilityId"]
            return _conflict_id
        except KeyError:
            return -1

    def get_sort_id(self, effect_id: int):
        try:
            _sort_id = self.effect_params.loc[effect_id, "overrideEffectId"]
            return _sort_id
        except KeyError:
            pass
        return -1

    def get_effect_name(self, effect_id: int) -> str:
        """Get the name of an effect by its ID."""
        if effect_id in [-1, 0, 4294967295]:
            return "Empty"
        if self.effect_name is None:
            self._load_text()
        try:
            row = self.effect_name[self.effect_name["id"] == effect_id]
            if not row.empty:
                return row["text"].values[0]
        except Exception:
            pass
        return f"Effect {effect_id}"

    def get_pool_effects(self, pool_id: int):
        if pool_id == -1:
            return []
        _effects = self.effect_table[self.effect_table["ID"] == pool_id]
        _effects = _effects["attachEffectId"].values.tolist()
        return _effects

    def get_pool_rollable_effects(self, pool_id: int):
        """Get effects that can actually roll in a pool (chanceWeight != 0).

        Effects with weight -65536 are disabled (cannot roll).
        Effects with weight 0 are class-specific effects that cannot naturally roll.
        Other weights (including other negative values) are valid rollable weights.

        For deep pools (2000000, 2100000, 2200000), returns effects that have
        rollable weight in ANY of the three deep pools, since the game appears
        to allow effects to roll on any deep relic if they're valid in any deep pool.
        """
        if pool_id == -1:
            return []

        # Deep pools are interchangeable - effect valid in any deep pool is valid for all
        deep_pools = {2000000, 2100000, 2200000}
        if pool_id in deep_pools:
            # Get effects with rollable weight in ANY deep pool
            _effects = self.effect_table[self.effect_table["ID"].isin(deep_pools)]
            _effects = df_filter_zero_chanceWeight(_effects)
            return _effects["attachEffectId"].unique().tolist()

        # For non-deep pools, check the specific pool
        _effects = self.effect_table[self.effect_table["ID"] == pool_id]
        # Filter out disabled (-65536) and zero-weight effects
        _effects = df_filter_zero_chanceWeight(_effects)
        return _effects["attachEffectId"].values.tolist()

    def get_pool_effects_strict(self, pool_id: int):
        """Get effects that can roll in a SPECIFIC pool (chanceWeight != 0).

        Unlike get_pool_rollable_effects(), this does NOT combine deep pools.
        Use this for strict validation to detect effects that are valid in some
        deep pool but not in the specific pool assigned to a relic.
        """
        if pool_id == -1:
            return []
        _effects = self.effect_table[self.effect_table["ID"] == pool_id]
        _effects = df_filter_zero_chanceWeight(_effects)
        return _effects["attachEffectId"].values.tolist()

    def get_effect_pools(self, effect_id: int):
        """Get all pool IDs that contain a specific effect."""
        _pools = self.effect_table[self.effect_table["attachEffectId"] == effect_id]
        return _pools["ID"].values.tolist()

    def get_effect_rollable_pools(self, effect_id: int):
        """Get all pool IDs where this effect can actually roll (chanceWeight != 0)."""
        _rows = self.effect_table[self.effect_table["attachEffectId"] == effect_id]
        # Filter out rows where chanceWeight is 0 (cannot roll)
        _rollable = df_filter_zero_chanceWeight(_rows)
        return _rollable["ID"].values.tolist()

    def is_deep_only_effect(self, effect_id: int):
        """Check if an effect only exists in deep relic pools (2000000, 2100000, 2200000)
        plus its own dedicated pool (effect_id == pool_id).
        These effects require curses when used on multi-effect relics."""
        if effect_id in [-1, 0, 4294967295]:
            return False
        pools = self.get_effect_pools(effect_id)
        deep_pools = {2000000, 2100000, 2200000}
        for pool in pools:
            # If pool is not a deep pool and not the effect's dedicated pool, it's not deep-only
            if pool not in deep_pools and pool != effect_id:
                return False
        return True

    def effect_needs_curse(self, effect_id: int) -> bool:
        """Check if an effect REQUIRES a curse.

        An effect needs a curse if it can ONLY roll from pool 2000000 (3-effect relics)
        and NOT from pools 2100000 or 2200000 (single-effect relics with no curse).

        We check rollable pools (weight != -65536) because an effect may be listed
        in a pool but with weight -65536 meaning it can't actually roll there.
        """
        if effect_id in [-1, 0, 4294967295]:
            return False

        # Get pools where this effect can actually roll
        pools = self.get_effect_rollable_pools(effect_id)

        # Pool 2000000 = 3-effect relics (always have curse slots)
        # Pools 2100000, 2200000 = single-effect relics (no curse slots)
        curse_required_pool = 2000000
        curse_free_pools = {2100000, 2200000}

        in_curse_required_pool = False
        in_curse_free_pool = False

        for pool in pools:
            if pool == effect_id:
                # Skip dedicated pool (effect's own pool)
                continue
            if pool == curse_required_pool:
                in_curse_required_pool = True
            elif pool in curse_free_pools:
                in_curse_free_pool = True

        # Effect needs curse only if it can roll from pool 2000000
        # AND cannot roll from any curse-free pool (2100000 or 2200000)
        return in_curse_required_pool and not in_curse_free_pool

    def get_adjusted_pool_sequence(self, relic_id: int,
                                   effects: list[int]):
        """
        Get adjusted pool sequence for a relic based on its effects.
        For each of the first three effects, check if it requires a curse.
        If it does, assign the next available curse pool ID.
        If it doesn't, assign -1.
        """
        effs = effects[:3]
        pool_ids = self.get_relic_pools_seq(relic_id)
        curse_pools = pool_ids[3:]
        new_pool_ids = pool_ids[:3]
        for i in range(3):
            if self.effect_needs_curse(effs[i]):
                new_pool_ids.append(curse_pools.pop(0))
            else:
                new_pool_ids.append(-1)
        return new_pool_ids

    def get_relic_slot_count(self, relic_id: int) -> tuple[int, int]:
        pool_seq: list = self.get_relic_pools_seq(relic_id)
        effect_slot = pool_seq[:3]
        curse_slot = pool_seq[3:]
        return 3-effect_slot.count(-1), 3-curse_slot.count(-1)

    def get_character_name(self, character_id: int):
        return self.npc_name[self.npc_name["id"] == character_id]["text"].values[0]

    def get_vessel_data(self, vessel_id: int):
        if self.antique_stand_param is None:
            return None
        _vessel_data = self.antique_stand_param[self.antique_stand_param["ID"] == vessel_id][
            ["goodsId", "heroType",
             "relicSlot1", "relicSlot2", "relicSlot3",
             "deepRelicSlot1", "deepRelicSlot2", "deepRelicSlot3",
             "unlockFlag"]
        ]
        # hero type start at 1, and 11 means ALL
        _hero_type = int(_vessel_data["heroType"].values[0])
        _unlock_flag = int(_vessel_data["unlockFlag"].values[0])
        _result = {"Name": self.vessel_names[self.vessel_names["id"] == _vessel_data["goodsId"].values[0]]["text"].values[0],
                   "Character": self.get_character_name(CHARACTER_NAME_ID[_hero_type-1]) if _hero_type != 11 else "All",
                   "Colors": (
                        COLOR_MAP[_vessel_data["relicSlot1"].values[0]],
                        COLOR_MAP[_vessel_data["relicSlot2"].values[0]],
                        COLOR_MAP[_vessel_data["relicSlot3"].values[0]],
                        COLOR_MAP[_vessel_data["deepRelicSlot1"].values[0]],
                        COLOR_MAP[_vessel_data["deepRelicSlot2"].values[0]],
                        COLOR_MAP[_vessel_data["deepRelicSlot3"].values[0]]
                        ),
                   "unlockFlag": _unlock_flag
                   }
        return _result


if __name__ == "__main__":
    source_data_handler = SourceDataHandler("zh_TW")
    t = source_data_handler.get_vessel_data(1000)
    print(t)
