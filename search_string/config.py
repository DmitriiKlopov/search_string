import os

import requests


PG_DB_HOST = os.environ.get("PG_DB_HOST", "10.1.25.101")
PG_DB_PORT = os.environ.get("PG_DB_PORT", "5432")
PG_DB_NAME = os.environ.get("PG_DB_NAME", "services_dev")
PG_DB_USER = os.environ.get("PG_DB_USER", "search-line-svc")
PG_DB_PASSWORD = os.environ.get("PG_DB_PASSWORD", "search-line-svc")

ES_HOST = os.environ.get("ELASTIC_HOST", "10.1.25.52")
ES_PORT = os.environ.get("ELASTIC_PORT", "9200")

CONFIGURATION_SERVICE_UUID = "0da757d6-af9c-4bc5-a2f7-5938a92f7a10"
CONFIGURATION_SCHEMA_UUID = "c22e7ec5-e917-4e32-843f-803bb987a411"
CONFIGURATION_DEV_VERSION_UUID = "88b23fba-869e-4b31-b71a-6a545129f1e0"
CONFIGURATION_TEST_VERSION_UUID = "67acbf0b-b755-4b3c-84cd-4af77485195e"
CONFIGURATION_LOCAL_VERSION_UUID = "732890fc-fe88-4098-ad5c-694185fdd753"

CONFIGURATION_BASE_URL = os.environ.get(
    "CONFIGURATION_BASE_URL",
    "http://configuration-editor.reesrtexp-dev.d.exportcenter.ru"
)
CONFIGURATION_BY_SCHEMA_URL = (
    "{base_url}/api/services/{service_uuid}/schemas/{schema_uuid}/settings"
)
CONFIGURATION_BY_VERSION_URL = "{base_url}/api/settings/{version_uuid}"
CONFIGURATION_VERSION_UUID = os.environ.get(
    "CONFIGURATION_VERSION_UUID",
    CONFIGURATION_TEST_VERSION_UUID
)


class SearchEngineConfig:
    def __init__(
        self,
        configuration_base_url=CONFIGURATION_BASE_URL,
        version_uuid=CONFIGURATION_VERSION_UUID
    ):
        self._configuration_base_url = configuration_base_url
        self._version_uuid = version_uuid

        # Вес индекса ТНВЭД 10
        self.tnved_10_idx_weight = 0
        # Вес индекса ТНВЭД 6
        self.tnved_6_idx_weight = 0
        # Вес индекса ГТД 10
        self.gtds_10_idx_weight = 0
        # Вес индекса HS
        self.hs_idx_weight = 0
        # Вес индекса ОКВЭД
        self.okved_idx_weight = 0

        # Вес приближенного поиска
        self.approx_search_weight = 0
        # Вес поиска по точному соответствию
        self.exact_search_weight = 0
        # Вес поиска по точному соответствию по подсловам
        self.exact_subsearch_weight = 0

        # Параметры для поиска по универсальному индексу
        # Вес точного поиска по фразам
        self.u_exact_phrase_search_weight = 0
        # Вес точного поиска по словам
        self.u_exact_word_search_weight = 0
        # Вес точного подпоиска по фразам
        self.u_exact_phrase_subsearch_weight = 0
        # Вес поиска с морфологией по фразам
        self.u_morphology_phrase_search_weight = 0
        # Вес поиска с морфологией по словам
        self.u_morphology_word_search_weight = 0
        # Вес поиска по подсловам с опечатками
        self.u_fuzziness_subsearch_weight = 0

        # Вес максимальной частоты упоминаний
        self.freq_weight = 0
        # Время жизни конфигурации в секундах
        self.lifetime = 0
        # Доля от максимального score, с которой результаты попадают на выдачу
        self.search_low_score_limit = 0
        # Время жизни ключевых слов
        self.keyword_lifetime = 0

        self.load_config()

    def load_config(self):
        try:
            url = CONFIGURATION_BY_VERSION_URL.format(
                base_url=self._configuration_base_url,
                version_uuid=self._version_uuid
            )
            with requests.get(url=url) as resp:
                loaded_config_dict = resp.json()['values']

            self.tnved_10_idx_weight = float(loaded_config_dict['tnved_10'])
            self.tnved_6_idx_weight = float(loaded_config_dict['tnved_6'])
            self.gtds_10_idx_weight = float(loaded_config_dict['gtds_10'])
            self.hs_idx_weight = float(loaded_config_dict['hs'])
            self.okved_idx_weight = float(loaded_config_dict['okved'])

            self.approx_search_weight = float(loaded_config_dict['approx_search'])
            self.exact_search_weight = float(loaded_config_dict['exact_search'])
            self.exact_subsearch_weight = float(loaded_config_dict['exact_subsearch'])

            self.u_exact_phrase_search_weight = float(loaded_config_dict['u_exact_phrase_search_weight'])
            self.u_exact_word_search_weight = float(loaded_config_dict['u_exact_word_search_weight'])
            self.u_exact_phrase_subsearch_weight = float(loaded_config_dict['u_exact_phrase_subsearch_weight'])
            self.u_morphology_phrase_search_weight = float(loaded_config_dict['u_morphology_phrase_search_weight'])
            self.u_morphology_word_search_weight = float(loaded_config_dict['u_morphology_word_search_weight'])
            self.u_fuzziness_subsearch_weight = float(loaded_config_dict['u_fuzziness_subsearch_weight'])

            self.freq_weight = float(loaded_config_dict['freq_weight'])
            self.lifetime = float(loaded_config_dict['lifetime'])
            self.search_low_score_limit = float(loaded_config_dict['search_low_score_limit'])
            self.keyword_lifetime = float(loaded_config_dict['keyword_lifetime'])
        except Exception:
            self.tnved_10_idx_weight = 0.5
            self.tnved_6_idx_weight = 1.0
            self.gtds_10_idx_weight = 0.4
            self.hs_idx_weight = 1.0
            self.okved_idx_weight = 1.0

            self.approx_search_weight = 1.0
            self.exact_search_weight = 5.0
            self.exact_subsearch_weight = 2.0

            self.u_exact_phrase_search_weight = 6.0
            self.u_exact_word_search_weight = 3.0
            self.u_exact_phrase_subsearch_weight = 4.0
            self.u_morphology_phrase_search_weight = 5.0
            self.u_morphology_word_search_weight = 2.0
            self.u_fuzziness_subsearch_weight = 1.0

            self.freq_weight = 1.5
            self.lifetime = 10.0
            self.search_low_score_limit = 0.15
            self.keyword_lifetime = 10.0
