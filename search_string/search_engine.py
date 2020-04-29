import math
import time
from contextlib import closing
from hashlib import md5

import psycopg2
from elasticsearch import Elasticsearch

from . import config


class SearchEngine:
    def __init__(self, settings):
        self.settings = settings
        self.symbols_en_to_ru = (u"qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOPASDFGHJKLZXCVBNM",
                                 u"йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗФЫВАПРОЛДЯЧСМИТЬ")
        self.translator_en_to_ru = {ord(eng): ord(rus) for eng, rus in zip(*self.symbols_en_to_ru)}
        self.symbols_ru_to_en = (u"йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ",
                                 u"qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP[]ASDFGHJKL;'ZXCVBNM,.")
        self.translator_ru_to_en = {ord(rus): ord(eng) for rus, eng in zip(*self.symbols_ru_to_en)}

        # Наименования блоков
        self.tnved_10_block_name = "tnved_10"
        self.tnved_block_name = "tnved"
        self.tnved_extra_block_name = "tnved_extra"
        self.okved_block_name = "okved"

        # Наименования индексов
        self.mat_index_name = "mat"
        self.tnved_10_index_name = "logstash_v2_tnved_10"
        self.tnved_6_index_name = "logstash_v3_tnved_6"
        self.gtds_10_index_name = "test_logstash_gtds_10_v2"
        self.hs_index_name = "logstash_v2_hs"
        self.okved_index_name = "logstash_v2_okved"

        # Максимальное количество выводимых результатов поиска
        self.max_shown_search_results_count = 20
        # Максимальное количество анализируемых результатов поиска
        self.max_analyzed_search_results_count = 50
        # Число проверяемых опечаток
        self.fuzziness_max_expansions = 1000

        # Словарь с весами индексов при поиске
        self.index_name_boost_dict = {self.tnved_10_index_name: settings.tnved_10_idx_weight,
                                      self.gtds_10_index_name: settings.gtds_10_idx_weight,
                                      self.tnved_6_index_name: settings.tnved_6_idx_weight,
                                      self.hs_index_name: settings.hs_idx_weight,
                                      self.okved_index_name: settings.okved_idx_weight}
        # Словарь с наименованиями индексов для отображения на фронте
        self.index_front_names_dict = {self.tnved_10_index_name: "ТНВЭД", self.gtds_10_index_name: "Практика",
                                       self.tnved_6_index_name: "ТНВЭД", self.hs_index_name: "HS",
                                       self.okved_index_name: "ОКВЭД"}
        # Вес точного поиска по фразам
        self.u_exact_phrase_search_weight = settings.u_exact_phrase_search_weight
        # Вес точного поиска по словам
        self.u_exact_word_search_weight = settings.u_exact_word_search_weight
        # Вес точного подпоиска по фразам
        self.u_exact_phrase_subsearch_weight = settings.u_exact_phrase_subsearch_weight
        # Вес поиска с морфологией по фразам
        self.u_morphology_phrase_search_weight = settings.u_morphology_phrase_search_weight
        # Вес поиска с морфологией по словам
        self.u_morphology_word_search_weight = settings.u_morphology_word_search_weight
        # Вес поиска по подсловам с опечатками
        self.u_fuzziness_subsearch_weight = settings.u_fuzziness_subsearch_weight

        # Подключение к эластику
        self.es = Elasticsearch(
            [{'host': config.ES_HOST, 'port': config.ES_PORT}],
            maxsize=25,
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniffer_timeout=60,
        )
        # Максимальные частоты упоминаний кодов на 6 знаках в источниках
        self.max_freq_dict = {self.tnved_10_index_name: 380, self.gtds_10_index_name: 70345}
        # Максимальный коэффициент увеличения score за счет частоты упоминаний
        self.freq_mult_coef = settings.freq_weight
        # Словарь с наименованиями индексов для поиска в зависимости от языка
        # {'ru': [список индексов для поиска на русском], 'en': [список индексов для поиска на английском]}
        self.block_index_names_dict = {self.tnved_block_name: {'ru': [self.tnved_6_index_name,
                                                                      self.tnved_10_index_name,
                                                                      self.gtds_10_index_name,
                                                                      self.hs_index_name],
                                                               'en': [self.hs_index_name,
                                                                      self.tnved_10_index_name,
                                                                      self.gtds_10_index_name,
                                                                      self.tnved_6_index_name]},
                                       self.okved_block_name: {'ru': [self.okved_index_name],
                                                               'en': [self.okved_index_name]},
                                       self.tnved_10_block_name: {'ru': [self.tnved_10_index_name,
                                                                         self.gtds_10_index_name],
                                                                  'en': [self.tnved_10_index_name,
                                                                         self.gtds_10_index_name]},
                                       self.tnved_extra_block_name: {'ru': [self.tnved_10_index_name,
                                                                            self.gtds_10_index_name],
                                                                     'en': [self.tnved_10_index_name,
                                                                            self.gtds_10_index_name]}
                                       }
        # Время жизни конфигурации в секундах
        self.lifetime = settings.lifetime
        # Время загрузки конфигурации
        self.load_time = time.time()
        # Доля от максимального score, с которой результаты попадают на выдачу
        self.search_low_score_limit = settings.search_low_score_limit
        # Время жизни ключевых слов
        self.keyword_lifetime = settings.keyword_lifetime
        # Время загрузки ключевых слов
        self.keyword_load_time = time.time()
        self._update_keywords()

    def set_config(self, settings):
        """ Задание конфигурации

        :param settings: параметры конфигурации
        :return:
        """
        self.settings = settings
        # Словарь с весами индексов при поиске
        self.index_name_boost_dict = {self.tnved_10_index_name: settings.tnved_10_idx_weight,
                                      self.gtds_10_index_name: settings.gtds_10_idx_weight,
                                      self.tnved_6_index_name: settings.tnved_6_idx_weight,
                                      self.hs_index_name: settings.hs_idx_weight,
                                      self.okved_index_name: settings.okved_idx_weight}
        # Вес точного поиска по фразам
        self.u_exact_phrase_search_weight = settings.u_exact_phrase_search_weight
        # Вес точного поиска по словам
        self.u_exact_word_search_weight = settings.u_exact_word_search_weight
        # Вес точного подпоиска по фразам
        self.u_exact_phrase_subsearch_weight = settings.u_exact_phrase_subsearch_weight
        # Вес поиска с морфологией по фразам
        self.u_morphology_phrase_search_weight = settings.u_morphology_phrase_search_weight
        # Вес поиска с морфологией по словам
        self.u_morphology_word_search_weight = settings.u_morphology_word_search_weight
        # Вес поиска по подсловам с опечатками
        self.u_fuzziness_subsearch_weight = settings.u_fuzziness_subsearch_weight

        # Максимальный коэффициент увеличения score за счет частоты упоминаний
        self.freq_mult_coef = settings.freq_weight
        # Время жизни конфигурации в секундах
        self.lifetime = settings.lifetime
        # Время загрузки конфигурации
        self.load_time = time.time()
        # Доля от максимального score, с которой результаты попадают на выдачу
        self.search_low_score_limit = settings.search_low_score_limit
        # Время жизни ключевых слов
        self.keyword_lifetime = settings.keyword_lifetime

    def _update_config(self):
        """ Обновление конфигурации

        :return:
        """
        self.settings.load_config()
        self.set_config(self.settings)

    def _update_keywords(self):
        """ Обновление ключевых слов в индексе tnved_6

        :return:
        """
        # Получение данных о ключевых словах из базы
        with closing(psycopg2.connect(dbname=config.PG_DB_NAME, user=config.PG_DB_USER,
                                      password=config.PG_DB_PASSWORD, host=config.PG_DB_HOST)) as conn:
            with conn.cursor() as cursor:
                # Выгружаем из базы коды товаров с ключевыми словами
                # Ключевые слова для кода прилетают в виде строк с разделителем |
                cursor.execute("select code, keyword from "
                               + "(select code, '' as keyword from search_line.elastic_tnved_6_keywords "
                               + "where code not in (select code from search_line.tnved_6_keywords) "
                               + "union select code, keyword from search_line.tnved_6_keywords "
                               + "where (code, keyword) not in "
                               + "(select code, keyword from search_line.elastic_tnved_6_keywords)) as t "
                               + "where code in (select code from search_line.tnved_6_names);")
                db_results = cursor.fetchall()
                for db_result in db_results:
                    doc_id = md5((db_result[0] + "_" + self.tnved_6_index_name).encode()).hexdigest()
                    self.es.update(index=self.tnved_6_index_name, id=doc_id, body={
                        "doc": {
                            "phrases": db_result[1].split("|")
                        }
                    })

                # Обновляем витрину с данными Эластика, синхронизируем ее с витриной для редактирования
                cursor.execute("refresh MATERIALIZED view concurrently search_line.elastic_tnved_6_keywords with data;")
                conn.commit()
        self.keyword_load_time = time.time()

    def search(self, search_string, block_names_str):
        """ Поиск по нескольким блокам

        :param search_string: содержимое поисковой строки.
        :param block_names_str: список индексов для поиска в виде строки через разделитель "|".
               Например, значение block_names_str может быть равно "tnved|okved".
        :return: список, состоящий из списков с результатами поиска по всем блокам.
        """
        # Обновляем конфигурацию, если время ее жизни истекло
        if time.time() - self.load_time >= self.lifetime:
            self._update_config()
        # Обновляем ключевые слова, если время их жизни истекло
        if time.time() - self.keyword_load_time >= self.keyword_lifetime:
            self._update_keywords()
        result = []
        block_names_list = block_names_str.split("|")
        for block_name in block_names_list:
            # Накапливаем результаты поиска по отдельным блокам
            if block_name in [self.tnved_10_block_name, self.tnved_block_name,
                              self.tnved_extra_block_name, self.okved_block_name]:
                result.append(self._one_block_search(block_name, search_string))
            else:
                result.append(self._one_block_search_universal(block_name, search_string))
        return result

    def search_extra(self, search_string, code):
        """ Определение выдачи для подсказки поиска ТНВЭД на 6 знаках, формируемой поиском на 10 знаках

        :param search_string: содержимое поисковой строки.
        :param code: выбранный 6-значный код.
        :return: результаты поиска по 10 знакам для кодов, начинающихся с выбранного 6-знака.
        """

        # Список пар: [имя индекса, результаты поиска в этом индексе]
        search_result_list = []

        # Определяем язык в поисковой строке
        language, search_string = self._get_search_line_language(self.tnved_extra_block_name, search_string)

        for search_index_name in self.block_index_names_dict[self.tnved_extra_block_name][language]:
            search_result = self._elastic_search(search_index_name,
                                                 self._get_search_extra_body(search_index_name,
                                                                             search_string,
                                                                             code,
                                                                             language))

            index_search_result = self._process_index_search_results(self.tnved_extra_block_name,
                                                                     search_index_name,
                                                                     search_result,
                                                                     is_code_search_mode=False)

            search_result_list.append([search_index_name, index_search_result])

        block_search_result = self._combine_block_search_results(self.tnved_extra_block_name, search_result_list, {})
        return block_search_result

    def _one_block_search(self, block_name, search_string):
        """ Поиск по одному из блоков ТНВЭД, ОКВЭД

        :param block_name: наименование блока.
        :param search_string: содержимое поисковой строки.
        :return: список словарей с результатами поиска.
        """
        if self._is_mat_inside(block_name, search_string):
            return [{"id": "", "block": "-", "header": "Обнаружены нецензурные выражения", "url": None,
                     "create_date": None, "score_block": None, "score_total": None}]
        else:
            is_code_search_mode = search_string.isnumeric()
            # Список пар: [имя индекса, результаты поиска в этом индексе]
            search_result_list = []

            if is_code_search_mode:
                language = 'ru'  # Для определенности
            else:
                # Определяем язык в поисковой строке
                language, search_string = self._get_search_line_language(block_name, search_string)
            # Результат поиска по фразам, пробрасываем дальше, чтобы точечно контролировать выдачу
            search_result_with_phrases = {}
            for search_index_name in self.block_index_names_dict[block_name][language]:
                search_result = self._elastic_search(search_index_name,
                                                     self._get_search_body(block_name,
                                                                           search_index_name,
                                                                           search_string,
                                                                           is_code_search_mode,
                                                                           is_phrase_search_mode=False,
                                                                           language=language))

                if search_index_name == self.tnved_6_index_name:
                    search_result_with_phrases = self._elastic_search(search_index_name,
                                                                      self._get_search_body(block_name,
                                                                                            search_index_name,
                                                                                            search_string,
                                                                                            is_code_search_mode=False,
                                                                                            is_phrase_search_mode=True,
                                                                                            language=language))
                    search_result_with_phrases = self._process_index_search_results(block_name,
                                                                                    search_index_name,
                                                                                    search_result_with_phrases,
                                                                                    is_code_search_mode=False)

                index_search_result = self._process_index_search_results(block_name,
                                                                         search_index_name,
                                                                         search_result,
                                                                         is_code_search_mode=is_code_search_mode)
                search_result_list.append([search_index_name, index_search_result])

            block_search_result = self._combine_block_search_results(block_name, search_result_list,
                                                                     search_result_with_phrases)
            return block_search_result

    def _one_block_search_universal(self, block_name, search_string):
        """ Поиск по одному из универсальных блоков

        :param block_name: наименование блока.
        :param search_string: содержимое поисковой строки.
        :return: список словарей с результатами поиска.
        """
        if self._is_mat_inside(block_name, search_string):
            return [{"id": "", "block": "-", "header": "Обнаружены нецензурные выражения", "url": None,
                     "create_date": None, "score_block": None, "score_total": None}]
        else:
            # Определяем язык в поисковой строке
            language, search_string = self._get_search_line_language(block_name, search_string)
            # Формируем имя индекса
            search_index_name = self._get_universal_index_name(block_name)
            # Начинаем поиски
            search_result_with_phrase = self._elastic_search(search_index_name,
                                                             self._get_search_universal_body(search_string,
                                                                                             language,
                                                                                             is_phrases_mode=True))
            search_result_no_phrase = self._elastic_search(search_index_name,
                                                           self._get_search_universal_body(search_string,
                                                                                           language,
                                                                                           is_phrases_mode=False))
            block_result = []
            search_no_phrase_max_score = 0
            if search_result_no_phrase["hits"]["total"]["value"] > 0:
                search_no_phrase_max_score = search_result_no_phrase["hits"]["max_score"]
            # Сначала записываем результаты, которые были найдены по фразам, с повышенным score
            for doc in search_result_with_phrase["hits"]["hits"]:
                if doc["_score"] > 0:
                    source = doc["_source"]
                    item = {
                        "id": source["id"],
                        "block": source["block"],
                        "header": source["header"],
                        "description": source["description"],
                        "url": source["url"],
                        "logo": {
                            "name": source["logo"]["name"],
                            "file-data": source["logo"]["file-data"],
                            "mime-type": source["logo"]["mime-type"],
                            "url": source["logo"]["url"]
                        },
                        "tags": source["tags"],
                        "create_date": source["create_date"],
                        "score": doc["_score"] + search_no_phrase_max_score,
                        "score_total": 0
                    }
                    block_result.append(item)
            for doc in search_result_no_phrase["hits"]["hits"]:
                if doc["_score"] >= self.search_low_score_limit * search_no_phrase_max_score:
                    source = doc["_source"]
                    item = {
                        "id": source["id"],
                        "block": source["block"],
                        "header": source["header"],
                        "description": source["description"],
                        "url": source["url"],
                        "logo": {
                            "name": source["logo"]["name"],
                            "file-data": source["logo"]["file-data"],
                            "mime-type": source["logo"]["mime-type"],
                            "url": source["logo"]["url"]
                        },
                        "tags": source["tags"],
                        "create_date": source["create_date"],
                        "score": doc["_score"],
                        "score_total": 0
                    }
                    block_result.append(item)
            if len(block_result) == 0:
                block_result.append(
                    {"id": "", "block": None, "tags": None, "header": "По запросу ничего не найдено", "url": None,
                     "create_date": None, "score_block": None, "score_total": None})
            return block_result

    def _process_index_search_results(self, block_name, index_name, search_result, is_code_search_mode):
        """ Обработка ответа Эластика, приведение к удобному для подсчетов виду

        :param block_name: наименование блока.
        :param index_name: наименование индекса.
        :param search_result: результаты приближенного поиска, точного поиска и точного "подпоиска".
        :return: словарь {код: [score; описание]} с результатами объединения.
        """
        # Словарь {код: [score; описание]}
        code_fields_dict = {}
        if not is_code_search_mode and (block_name == self.tnved_block_name and index_name == self.tnved_10_index_name
                                        or index_name == self.gtds_10_index_name):
            buckets = search_result["aggregations"]["custom"]["buckets"]
            for doc in buckets:
                if doc["score_max"]["value"] > 0:
                    code_fields_dict[doc["key"]] = [
                        doc["score_max"]["value"] *
                        (1 + (self.freq_mult_coef - 1) * float(doc["doc_count"]) / self.max_freq_dict[index_name]),
                        "doc_count = " + str(doc["doc_count"])]
        else:
            hits = search_result["hits"]["hits"]
            for doc in hits:
                source = doc["_source"]
                # Проверяем на положительный score, потому что параметр запроса boost мог его обнулить
                if doc["_score"] > 0:
                    code_fields_dict[source["code"]] = [
                        doc["_score"],
                        source["description"]]
        return code_fields_dict

    def _combine_block_search_results(self, block_name, search_result_list, search_result_with_phrases):
        """ Объединение результатов поиска в одном блоке

        :param block_name: наименование блока.
        :param search_result_list: список пар [имя индекса, результаты поиска в этом индексе].
        :return: результаты поиска по блоку.
        """
        # Словарь code_fields_dict: {код: [score; описание; список с индексами, в которых код нашелся]}
        # Объединяем результаты поиска в разных индексах
        code_fields_dict = {}
        for search_result_pair in search_result_list:
            index_name = search_result_pair[0]
            index_search_result = search_result_pair[1]
            for code in index_search_result.keys():
                if code not in code_fields_dict.keys():
                    code_fields_dict[code] = [index_search_result[code][0] * self.index_name_boost_dict[index_name],
                                              index_search_result[code][1],
                                              [index_name]]
                else:
                    # увеличиваем score; оставляем первое описание; добавляем индекс в найденные
                    code_fields_dict[code] = [
                        code_fields_dict[code][0] + index_search_result[code][0] * self.index_name_boost_dict[
                            index_name],
                        code_fields_dict[code][1],
                        code_fields_dict[code][2] + [index_name]]
        # Добавляем в смешанную выдачу результаты поиска по фразам
        # Максимальный score в текущей выдаче
        current_max_score = 0
        if len(code_fields_dict) > 0:
            current_max_score = max([value[0] for value in code_fields_dict.values()])
        for code in search_result_with_phrases.keys():
            if code not in code_fields_dict.keys():
                code_fields_dict[code] = [search_result_with_phrases[code][0] + current_max_score,
                                          search_result_with_phrases[code][1],
                                          [self.tnved_6_index_name]]
            else:
                code_fields_dict[code] = [
                    math.log10(1.1 + code_fields_dict[code][0])
                    + search_result_with_phrases[code][0] + current_max_score,
                    code_fields_dict[code][1],
                    code_fields_dict[code][2] + [self.tnved_6_index_name]]
        # Упорядочиваем результаты по убыванию score
        sorted_results = sorted(code_fields_dict.items(), key=lambda x: x[1][0], reverse=True)
        # Максимальный score в результирующей выдаче
        full_max_score = 0
        if len(sorted_results) > 0:
            full_max_score = sorted_results[0][1][0]
        # Фильтруем результаты по нижнему порогу score
        sorted_results = list(filter(lambda x: x[1][0] >= full_max_score * self.search_low_score_limit, sorted_results))
        # Формируем конечную выдачу, при необходимости подтягвая наименования из базы
        hit_num = 0
        block_result = []
        if block_name == self.tnved_block_name or block_name == self.tnved_10_block_name:
            if block_name == self.tnved_block_name:
                table_name = 'tnved_6_names'
            else:
                table_name = 'tnved_10_names'
            values_list = []
            for code, fields in sorted_results:
                values_list.append("('" + str(code) + "', " + str(fields[0]) + ", '" + "|".join(
                    list(set([self.index_front_names_dict[name] for name in fields[2]]))) + "')")
                hit_num += 1
            if hit_num > 0:
                with closing(psycopg2.connect(dbname=config.PG_DB_NAME, user=config.PG_DB_USER,
                                              password=config.PG_DB_PASSWORD, host=config.PG_DB_HOST)) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("WITH cs(code, score, tags) AS (VALUES " + ", ".join(values_list) + ")\n"
                                       + "select hrh.code as code, hrh.description as description, cs.score, cs.tags "
                                         "from search_line." + table_name + " as hrh\n"
                                                                            "INNER JOIN cs on hrh.code=cs.code order by cs.score desc;")

                        db_results = cursor.fetchall()
                        hit_num = 0
                        for db_result in db_results:
                            item = {"id": str(db_result[0]), "block": block_name,
                                    "tags": db_result[3].split("|"),
                                    "header": db_result[1], "url": None,
                                    "create_date": None, "score_block": str(db_result[2]),
                                    "score_total": str(db_result[2])}

                            block_result.append(item)
                            hit_num += 1
                            if hit_num == self.max_shown_search_results_count:
                                break
            else:
                block_result.append(
                    {"id": "", "block": None, "tags": None, "header": "По запросу ничего не найдено", "url": None,
                     "create_date": None, "score_block": None, "score_total": None})
        elif block_name == self.okved_block_name:
            hit_num = 0
            for code, fields in sorted_results:
                item = {"id": self._add_dots_to_okved_code(code), "block": block_name, "tags": "ОКВЭД",
                        "header": fields[1], "url": None,
                        "create_date": None, "score_block": str(fields[0]), "score_total": str(fields[0])}
                block_result.append(item)
                hit_num += 1
                if hit_num == self.max_shown_search_results_count:
                    break
            if hit_num == 0:
                block_result.append(
                    {"id": "", "block": None, "tags": None, "header": "По запросу ничего не найдено", "url": None,
                     "create_date": None, "score_block": None, "score_total": None})
        elif block_name == self.tnved_extra_block_name:
            values_list = []
            for code, fields in sorted_results:
                values_list.append("('" + str(code) + "', " + str(fields[0]) + ", '" + "|".join(
                    list(set([self.index_front_names_dict[name] for name in fields[2]]))) + "')")
                hit_num += 1
            if hit_num > 0:
                with closing(psycopg2.connect(dbname=config.PG_DB_NAME, user=config.PG_DB_USER,
                                              password=config.PG_DB_PASSWORD, host=config.PG_DB_HOST)) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("WITH cs(code, score, tags) AS (VALUES " + ", ".join(values_list) + ")\n"
                                       + "select hrh.code as code, hrh.description as description, cs.score, cs.tags "
                                         "from search_line.tnved_10_names as hrh\n"
                                         "INNER JOIN cs on hrh.code=cs.code order by cs.score desc;")

                        db_results = cursor.fetchall()
                        hit_num = 0
                        for db_result in db_results:
                            item = "Код ТНВЭД: " + str(db_result[0]) + "\n"
                            item += "Описание ТНВЭД: " + db_result[1] + "\n"
                            block_result.append(item)
                            hit_num += 1
                            if hit_num == self.max_shown_search_results_count:
                                break
            else:
                block_result.append("По запросу ничего не найдено")
        return block_result

    def _elastic_search(self, index_name, search_body):
        """Поиск в Эластике

        :param index_name: имя индекса для поиска.
        :param search_body: тело запроса.
        :return: словарь с доп. информацией и результатами поиска.
        """
        return self.es.search(index=index_name, body=search_body)

    def _get_search_line_language(self, block_name, search_string):
        """ Определение языка в поисковой строке

        :param block_name: наименование блока.
        :param search_string: содержимое поисковой строки.
        :return: язык, по которому были найдены "лучшие" результаты вместе со строкой поиска в нужном языке
        """
        # Нужно рассматривать два случая для русского, потому что транслятор из знаков препинания делает буквы
        search_string_ru_initial = search_string
        search_string_ru_translated = search_string.translate(self.translator_en_to_ru)
        search_string_en = search_string.translate(self.translator_ru_to_en)
        # Разделяем на определение языка в универсальном блоке и нет
        if block_name in [self.tnved_10_block_name, self.tnved_block_name,
                          self.tnved_extra_block_name, self.okved_block_name]:
            search_result_ru_initial = self._elastic_search(self.gtds_10_index_name,
                                                            self._get_search_body(self.tnved_block_name,
                                                                                  self.gtds_10_index_name,
                                                                                  search_string_ru_initial,
                                                                                  is_code_search_mode=False,
                                                                                  is_phrase_search_mode=False,
                                                                                  language="ru"))
            search_result_ru_translated = self._elastic_search(self.gtds_10_index_name,
                                                               self._get_search_body(self.tnved_block_name,
                                                                                     self.gtds_10_index_name,
                                                                                     search_string_ru_translated,
                                                                                     is_code_search_mode=False,
                                                                                     is_phrase_search_mode=False,
                                                                                     language="ru"))
            search_string_ru, search_result_ru = self._get_best_russian_search_result(search_string_ru_initial,
                                                                                      search_result_ru_initial,
                                                                                      search_string_ru_translated,
                                                                                      search_result_ru_translated)

            search_result_en = self._elastic_search(self.hs_index_name,
                                                    self._get_search_body(self.tnved_block_name,
                                                                          self.hs_index_name,
                                                                          search_string_en,
                                                                          is_code_search_mode=False,
                                                                          is_phrase_search_mode=False,
                                                                          language="en"))
        else:
            # Сначала определяем язык по фразам, у них наибольший приоритет
            search_result_ru_initial = self._elastic_search(self._get_universal_index_name(block_name),
                                                            self._get_search_universal_body(search_string_ru_initial,
                                                                                            "ru",
                                                                                            is_phrases_mode=True))
            search_result_ru_translated = self._elastic_search(self._get_universal_index_name(block_name),
                                                               self._get_search_universal_body(
                                                                   search_string_ru_translated,
                                                                   "ru",
                                                                   is_phrases_mode=True))
            search_string_ru, search_result_ru = self._get_best_russian_search_result(search_string_ru_initial,
                                                                                      search_result_ru_initial,
                                                                                      search_string_ru_translated,
                                                                                      search_result_ru_translated)

            search_result_en = self._elastic_search(self._get_universal_index_name(block_name),
                                                    self._get_search_universal_body(search_string_en,
                                                                                    "en",
                                                                                    is_phrases_mode=True))

        hits_ru = search_result_ru["hits"]
        hits_en = search_result_en["hits"]
        if hits_ru["total"]["value"] > 0 and hits_en["total"]["value"] > 0:
            if hits_ru["max_score"] >= hits_en["max_score"]:
                return "ru", search_string_ru
            else:
                return "en", search_string_en
        elif hits_ru["total"]["value"] > 0:
            return "ru", search_string_ru
        elif hits_en["total"]["value"] > 0:
            return "en", search_string_en
        else:
            # Разделяем на определение языка в универсальном блоке и нет
            if block_name in [self.tnved_10_block_name, self.tnved_block_name,
                              self.tnved_extra_block_name, self.okved_block_name]:
                # Здесь по-хорошему нужно сверяться с поиском по tnved_6
                # На случай, если именование отсутствует в ГТД, но есть в справочнике ТНВЭД
                # На русском не ищем, оптому что этот поиск осуществлялся на предыдущем шаге
                search_result_en = self._elastic_search(self.hs_index_name,
                                                        self._get_search_body(self.tnved_block_name,
                                                                              self.gtds_10_index_name,
                                                                              search_string_en,
                                                                              is_code_search_mode=False,
                                                                              is_phrase_search_mode=False,
                                                                              language="en"))
            else:
                # Здесь уже определяем язык больше по содержимому текстовых полей, не даем фразам приоритет
                search_result_ru_initial = self._elastic_search(self._get_universal_index_name(block_name),
                                                                self._get_search_universal_body(
                                                                    search_string_ru_initial,
                                                                    "ru",
                                                                    is_phrases_mode=False))
                search_result_ru_translated = self._elastic_search(self._get_universal_index_name(block_name),
                                                                   self._get_search_universal_body(
                                                                       search_string_ru_translated,
                                                                       "ru",
                                                                       is_phrases_mode=False))
                search_string_ru, search_result_ru = self._get_best_russian_search_result(search_string_ru_initial,
                                                                                          search_result_ru_initial,
                                                                                          search_string_ru_translated,
                                                                                          search_result_ru_translated)

                search_result_en = self._elastic_search(self._get_universal_index_name(block_name),
                                                        self._get_search_universal_body(search_string_en,
                                                                                        "en",
                                                                                        is_phrases_mode=False))

            hits_ru = search_result_ru["hits"]
            hits_en = search_result_en["hits"]
            if hits_ru["total"]["value"] > 0 and hits_en["total"]["value"] > 0:
                if hits_ru["max_score"] >= hits_en["max_score"]:
                    return "ru", search_string_ru
                else:
                    return "en", search_string_en
            elif hits_ru["total"]["value"] > 0:
                return "ru", search_string_ru
            elif hits_en["total"]["value"] > 0:
                return "en", search_string_en
            else:
                # Когда нигде ничего не нашлось
                return "ru", search_string_ru

    def _get_search_body(self, block_name, index_name, search_string, is_code_search_mode,
                         is_phrase_search_mode, language):
        """ Формирование тела запроса для поиска в Elastic

        :param block_name: наименование блока.
        :param index_name: наименование индекса.
        :param search_string: содержимое поисковой строки.
        :param is_code_search_mode: флаг поиска по коду, True - поиск по коду, False - поиск по содержимому.
        :param language: используемый язык (ru или en).
        :return: тело для запроса в Elastic.
        """
        size = self.max_analyzed_search_results_count
        if block_name == self.tnved_10_block_name:
            aggregation_code_length = '10'
        else:
            aggregation_code_length = '6'
        if is_code_search_mode:
            return {
                "size": size,
                "query": {
                    "match": {
                        "code": {
                            "query": search_string
                        }
                    }
                }
            }
        elif index_name == self.mat_index_name:
            return {
                "query": {
                    "match": {
                        "phrase": {
                            "query": search_string
                        }
                    }
                }
            }
        elif is_phrase_search_mode:
            return {
                "query": {
                    "multi_match": {
                        "query": search_string,
                        "fields": ["phrases"],
                        "type": "phrase"
                    }
                }
            }
        elif index_name == self.tnved_10_index_name and block_name == self.tnved_block_name or \
                index_name == self.gtds_10_index_name:
            return {
                "size": 1,
                "query": {
                    "bool": {
                        "should": self._get_tnved_search_body_should_part(search_string, language)
                    }
                },
                "aggregations": {
                    "custom": {
                        "terms": {
                            "field": "code_" + aggregation_code_length,
                            "order": {"score_max": "desc"}
                        },
                        "aggregations": {
                            "score_sum": {"sum": {"script": "_score"}},
                            "score_max": {"max": {"script": "_score"}}
                        }
                    }
                }
            }
        elif index_name == self.tnved_6_index_name or index_name == self.hs_index_name or \
                index_name == self.okved_index_name or index_name == self.tnved_10_index_name and \
                block_name == self.tnved_10_block_name:
            return {
                "size": size,
                "query": {
                    "bool": {
                        "should": self._get_tnved_search_body_should_part(search_string, language)
                    }
                }
            }

    def _get_search_extra_body(self, index_name, search_string, code, language):
        """ Формирование тела запроса для поиска в Elastic для формирования подсказки

        :param index_name: наименование индекса.
        :param search_string: содержимое поисковой строки.
        :param code: выбранный 6-значный код товара.
        :param language: используемый язык (ru или en).
        :return: тело для запроса в Elastic.
        """
        size = self.max_analyzed_search_results_count
        if index_name == self.tnved_10_index_name:
            return {
                "size": size,
                "query": {
                    "bool": {
                        "must": {
                            "match": {"code": code}
                        },
                        "should": self._get_tnved_search_body_should_part(search_string, language)
                    }
                }
            }
        else:
            return {
                "size": 0,
                "query": {
                    "bool": {
                        "must": {
                            "match": {"code": code}
                        },
                        "should": self._get_tnved_search_body_should_part(search_string, language)
                    }
                },
                "aggregations": {
                    "custom": {
                        "terms": {
                            "field": "code_10",
                            "order": {"score_max": "desc"}
                        },
                        "aggregations": {
                            "score_sum": {"sum": {"script": "_score"}},
                            "score_max": {"max": {"script": "_score"}}
                        }
                    }
                }
            }

    def _get_search_universal_body(self, search_string, language, is_phrases_mode):
        """ Формирование тела запроса для поиска в универсальном индексе

        :param search_string: содержимое поисковой строки.
        :param language: используемый язык (ru или en).
        :param is_phrases_mode: флаг более приоритетного поиска по фразам.
        :return: тело для запроса в Elastic для поиска в универсальном индексе.
        """
        size = self.max_shown_search_results_count
        # Если в режиме поиска по фразам, то делаем их обязательными на вхождение, иначе обязательно пропускаем
        if is_phrases_mode:
            phrase_logical_operator = "must"
        else:
            phrase_logical_operator = "must_not"
        return {
            "size": size,
            "query": {
                "bool": {
                    phrase_logical_operator: [
                        {
                            "match": {
                                "phrases": {
                                    "query": search_string,
                                    "boost": 1
                                }
                            }
                        }
                    ],
                    "should": [
                        {
                            "multi_match": {
                                "query": search_string,
                                "fields": ["fulltext.fulltext_exact"],
                                "type": "phrase",
                                "slop": 1,
                                "boost": self.u_exact_phrase_search_weight
                            }
                        },
                        {
                            "multi_match": {
                                "query": search_string,
                                "fields": ["fulltext.fulltext_exact"],
                                "boost": self.u_exact_word_search_weight
                            }
                        },
                        {
                            "multi_match": {
                                "query": search_string,
                                "fields": ["fulltext.fulltext_sub_exact"],
                                "type": "phrase",
                                "slop": 1,
                                "boost": self.u_exact_phrase_subsearch_weight
                            }
                        },
                        {
                            "multi_match": {
                                "query": search_string,
                                "fields": ["fulltext.fulltext_" + language + "_morphology"],
                                "type": "phrase",
                                "slop": 1,
                                "boost": self.u_morphology_phrase_search_weight
                            }
                        },
                        {
                            "multi_match": {
                                "query": search_string,
                                "fields": ["fulltext.fulltext_" + language + "_morphology"],
                                "boost": self.u_morphology_word_search_weight
                            }
                        },
                        {
                            "multi_match": {
                                "query": search_string,
                                "operator": "and",
                                "fields": ["fulltext.fulltext_" + language + "_fuzziness"],
                                "type": "most_fields",
                                "fuzziness": "AUTO",
                                "max_expansions": self.fuzziness_max_expansions,
                                "boost": self.u_fuzziness_subsearch_weight
                            }
                        }
                    ]
                }
            }
        }

    def _get_tnved_search_body_should_part(self, search_string, language):
        # Основная часть тела запроса к Эластику для поиска по ТНВЭД
        return [
            {
                "multi_match": {
                    "query": search_string,
                    "fields": ["description.description_exact"],
                    "type": "phrase",
                    "slop": 1,
                    "boost": self.u_exact_phrase_search_weight
                }
            },
            {
                "multi_match": {
                    "query": search_string,
                    "operator": "and",
                    "fields": ["description.description_exact"],
                    "boost": self.u_exact_word_search_weight
                }
            },
            {
                "multi_match": {
                    "query": search_string,
                    "fields": ["description.description_sub_exact"],
                    "type": "phrase",
                    "slop": 1,
                    "boost": self.u_exact_phrase_subsearch_weight
                }
            },
            {
                "multi_match": {
                    "query": search_string,
                    "fields": ["description.description_" + language + "_morphology"],
                    "type": "phrase",
                    "slop": 1,
                    "boost": self.u_morphology_phrase_search_weight
                }
            },
            {
                "multi_match": {
                    "query": search_string,
                    "operator": "and",
                    "fields": ["description.description_" + language + "_morphology"],
                    "boost": self.u_morphology_word_search_weight
                }
            },
            {
                "multi_match": {
                    "query": search_string,
                    "operator": "and",
                    "fields": ["description.description_" + language + "_fuzziness"],
                    "type": "most_fields",
                    "fuzziness": "AUTO",
                    "max_expansions": self.fuzziness_max_expansions,
                    "boost": self.u_fuzziness_subsearch_weight
                }
            }
        ]

    def _is_mat_inside(self, block_name, search_string):
        """ Проверка наличия мата в строке

        :param block_name: наименование блока.
        :param search_string: содержимое поисковой строки.
        :return: False - мат не обнаружен, True - мат обнаружен.
        """
        return self._elastic_search(self.mat_index_name,
                                    self._get_search_body(block_name,
                                                          self.mat_index_name,
                                                          search_string,
                                                          is_code_search_mode=False,
                                                          is_phrase_search_mode=False,
                                                          language="ru"))["hits"]["total"]["value"] > 0 \
               or self._elastic_search(self.mat_index_name,
                                       self._get_search_body(block_name,
                                                             self.mat_index_name,
                                                             search_string.translate(self.translator_en_to_ru),
                                                             is_code_search_mode=False,
                                                             is_phrase_search_mode=False,
                                                             language="ru"))["hits"]["total"]["value"] > 0

    @staticmethod
    def _add_dots_to_okved_code(code_str):
        """ Вставка в строку с кодом ОКВЭД разделителей-точек

        :param code_str: строка с кодом ОКВЭД без разделителей "12002".
        :return: строка с кодом ОКВЭД с разделителями "12.00.2".
        """
        code_str_with_dots = ""
        for i in range(len(code_str)):
            if i > 0 and i % 2 == 0:
                code_str_with_dots += "."
            code_str_with_dots += code_str[i]
        return code_str_with_dots

    @staticmethod
    def _get_universal_index_name(block_name):
        """ Формирование имени индекса для универсального поиска по наименованию блока

        :param block_name: наименование блока.
        :return: имя индекса для универсального поиска
        """
        symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
                   u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")
        translator = {ord(rus): ord(eng) for rus, eng in zip(*symbols)}
        block_name = block_name.lower()
        index_name = ""
        for char in block_name:
            if char.isalpha() or char.isnumeric():
                index_name += char
            else:
                index_name += "_"
        return "universal_" + index_name.translate(translator)

    @staticmethod
    def _get_best_russian_search_result(search_string1, search_result1, search_string2, search_result2):
        if search_result1["hits"]["total"]["value"] > 0 and search_result2["hits"]["total"]["value"] > 0:
            if search_result1["hits"]["max_score"] >= search_result2["hits"]["max_score"]:
                return search_string1, search_result1
            else:
                return search_string2, search_result2
        elif search_result1["hits"]["total"]["value"] > 0:
            return search_string1, search_result1
        elif search_result2["hits"]["total"]["value"] > 0:
            return search_string2, search_result2
        else:
            # Когда нигде ничего не нашлось
            return search_string1, search_result1
