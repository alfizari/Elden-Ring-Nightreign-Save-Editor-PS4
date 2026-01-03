import pandas as pd
import pathlib
from typing import Optional


COLOR_MAP = ["Red", "Blue", "Yellow", "Green"]
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


class SourceDataHandler:
    WORKING_DIR = pathlib.Path(__file__).parent.resolve()
    PARAM_DIR = pathlib.Path(WORKING_DIR / "Resources/Param")
    TEXT_DIR = pathlib.Path(WORKING_DIR / "Resources/Text")
    RELIC_TEXT_FILE_NAME = ["AntiqueName.fmg.xml", "AntiqueName_dlc01.fmg.xml"]
    EFFECT_NAME_FILE_NAMES = [
        "AttachEffectName.fmg.xml",
        "AttachEffectName_dlc01.fmg.xml",
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
            self.effect_table[["ID", "attachEffectId", "chanceWeight"]]

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

        self.relic_name: Optional[pd.DataFrame] = None
        self.effect_name: Optional[pd.DataFrame] = None
        self._load_text(language)

    def _load_text(self, language: str = "en_US"):
        support_languages = LANGUAGE_MAP.keys()
        _lng = language
        if language not in support_languages:
            _lng = "en_US"
        # Deal with Relic text
        # Read all Relic xml from language subfolder
        _relic_names: Optional[pd.DataFrame] = None
        for file_name in SourceDataHandler.RELIC_TEXT_FILE_NAME:
            _df = pd.read_xml(
                SourceDataHandler.TEXT_DIR / _lng / file_name,
                xpath="/fmg/entries/text"
            )
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

    def get_effect_conflict_id(self, effect_id: int):
        try:
            if effect_id == -1 or effect_id == 4294967295:
                return -1
            _conflict_id = self.effect_params.loc[effect_id, "compatibilityId"]
            return _conflict_id
        except KeyError:
            return -1

    def get_sort_id(self, effect_id: int):
        _sort_id = self.effect_params.loc[effect_id, "overrideEffectId"]
        return _sort_id

    def get_pool_effects(self, pool_id: int):
        if pool_id == -1:
            return []
        _effects = self.effect_table[self.effect_table["ID"] == pool_id]
        _effects = _effects["attachEffectId"].values.tolist()
        return _effects

    def get_effect_pools(self, effect_id: int):
        """Get all pool IDs that contain a specific effect."""
        _pools = self.effect_table[self.effect_table["attachEffectId"] == effect_id]
        return _pools["ID"].values.tolist()

    def get_effect_rollable_pools(self, effect_id: int):
        """Get all pool IDs where this effect can actually roll (chanceWeight != -65536)."""
        _rows = self.effect_table[self.effect_table["attachEffectId"] == effect_id]
        # Filter out rows where chanceWeight is -65536 (cannot roll)
        _rollable = _rows[_rows["chanceWeight"] != -65536]
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


if __name__ == "__main__":
    source_data_handler = SourceDataHandler("zh_TW")
    t = source_data_handler.get_effect_origin_structure()
    print(t)
