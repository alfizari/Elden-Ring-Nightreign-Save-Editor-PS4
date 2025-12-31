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
            self.effect_table[["ID", "attachEffectId"]]

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
                _result[str(index)] = {
                    "name": _copy_df.loc[index, "name"],
                    "color": COLOR_MAP[
                        int(self.relic_table.loc[index, "relicColor"])
                        ],
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
        _reslut = {}
        for index, row in self.effect_params.iterrows():
            try:
                _attachTextId = self.effect_params.loc[index, "attachTextId"]
                _reslut[str(index)] = {
                    "name": _copy_df.loc[
                        _attachTextId, "text"
                    ]
                }
            except KeyError:
                _reslut[str(index)] = {"name": "Unknown"}
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
        _conflict_id = self.effect_params.loc[effect_id, "compatibilityId"]
        return _conflict_id

    def get_sort_id(self, effect_id: int):
        _sort_id = self.effect_params.loc[effect_id, "overrideEffectId"]
        return _sort_id

    def get_pool_effects(self, pool_id: int):
        if pool_id == -1:
            return []
        _effects = self.effect_table[self.effect_table["ID"] == pool_id]
        _effects = _effects["attachEffectId"].values.tolist()
        return _effects


if __name__ == "__main__":
    source_data_handler = SourceDataHandler("zh_TW")
    t = source_data_handler.get_relic_pools_seq(202)
    print(t)
