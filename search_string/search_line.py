from elasticsearch import Elasticsearch
import psycopg2
from contextlib import closing

symbols_en_to_ru = (u"qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOPASDFGHJKLZXCVBNM",
                    u"йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗФЫВАПРОЛДЯЧСМИТЬ")
translator_en_to_ru = {ord(eng): ord(rus) for eng, rus in zip(*symbols_en_to_ru)}
symbols_ru_to_en = (u"йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ",
                    u"qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP[]ASDFGHJKL;'ZXCVBNM,.")
translator_ru_to_en = {ord(rus): ord(eng) for rus, eng in zip(*symbols_ru_to_en)}

# tnved_10_index_name = "new_tnved_10"
# tnved_6_index_name = "new_tnved_6"
# gtds_10_index_name = "gtds_10"
# gtds_6_index_name = "new_gtds_6"
# hs_index_name = "new_hs"
tnved_10_index_name = "logstash_tnved_10"
tnved_6_index_name = "logstash_tnved_6"
gtds_10_index_name = "logstash_gtds_10"
gtds_6_index_name = "logstash_gtds_6"
hs_index_name = "logstash_hs"
index_names = [tnved_10_index_name, gtds_10_index_name, tnved_6_index_name, gtds_6_index_name, hs_index_name]
index_boosts = [1.0, 0.8, 1.0, 0.8, 0.8]
search_index_names = [tnved_6_index_name, gtds_6_index_name, hs_index_name]
index_name_boost_dict = {}
for i in range(len(index_names)):
    index_name_boost_dict[index_names[i]] = index_boosts[i]
# первый показатель - приближенный поиск, второй - поиск по точному соответствию
one_index_search_results_boost_list = [1.0, 2.0]
# подключение к эластику удаленно или локально
es = Elasticsearch([{'host': '10.1.25.52', 'port': '9200'}])


# es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])


# rename into get_all_results_search_body
def get_search_body(index_name, search_string, is_code_search_mode, is_exact_mode, language):
    # количество генерируемых вариантов опечаток
    size = 50
    fuzziness_max_expansions = 1000
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
    elif language == "en":
        if index_name == hs_index_name:
            if not is_exact_mode:
                return {
                    "size": size,
                    "query": {
                        "match": {
                            "description_en": {
                                "query": search_string.translate(translator_ru_to_en),
                                "fuzziness": "AUTO",
                                "max_expansions": fuzziness_max_expansions
                            }
                        }
                    }
                }
            else:
                return {
                    "size": size,
                    "query": {
                        "match": {
                            "description_en_exact": {
                                "query": search_string.translate(translator_ru_to_en)
                            }
                        }
                    }
                }
        elif index_name == "mat":
            return {
                "query": {
                    "match": {
                        "phrase": {
                            "query": search_string.translate(translator_ru_to_en)
                        }
                    }
                }
            }
        else:
            if not is_exact_mode:
                return {
                    "size": size,
                    "query": {
                        "match": {
                            "description_en": {
                                "query": search_string.translate(translator_ru_to_en),
                                "fuzziness": "AUTO",
                                "max_expansions": fuzziness_max_expansions
                            }
                        }
                    }
                }
            else:
                return {
                    "size": size,
                    "query": {
                        "match": {
                            "description_en_exact": {
                                "query": search_string.translate(translator_ru_to_en)
                            }
                        }
                    }
                }
    else:
        if index_name == hs_index_name:
            if not is_exact_mode:
                return {
                    "size": size,
                    "query": {
                        "match": {
                            "description_ru": {
                                "query": search_string.translate(translator_en_to_ru),
                                "fuzziness": "AUTO",
                                "max_expansions": fuzziness_max_expansions
                            }
                        }
                    }
                }
            else:
                return {
                    "size": size,
                    "query": {
                        "match": {
                            "description_ru_exact": {
                                "query": search_string.translate(translator_en_to_ru)
                            }
                        }
                    }
                }
        elif index_name == "mat":
            return {
                "query": {
                    "match": {
                        "phrase": {
                            "query": search_string.translate(translator_en_to_ru)
                        }
                    }
                }
            }
        else:
            if not is_exact_mode:
                return {
                    "size": size,
                    "query": {
                        "match": {
                            "description_ru": {
                                "query": search_string.translate(translator_en_to_ru),
                                "fuzziness": "AUTO",
                                "max_expansions": fuzziness_max_expansions
                            }
                        }
                    }
                }
            else:
                return {
                    "size": size,
                    "query": {
                        "match": {
                            "description_ru_exact": {
                                "query": search_string.translate(translator_en_to_ru)
                            }
                        }
                    }
                }


def get_one_result_search_body(search_string, code, is_exact_mode, language):
    fuzziness_max_expansions = 1000
    if language == "en":
        if not is_exact_mode:
            return {
                "query": {
                    "bool": {
                        "must": {
                            "match": {"code": code}
                        },
                        "should": {
                            "match": {
                                "description_en": {
                                    "query": search_string.translate(translator_ru_to_en),
                                    "fuzziness": "AUTO",
                                    "max_expansions": fuzziness_max_expansions
                                }
                            }
                        }
                    }
                }
            }
        else:
            return {
                "query": {
                    "bool": {
                        "must": {
                            "match": {"code": code}
                        },
                        "should": {
                            "match": {
                                "description_en_exact": {"query": search_string.translate(translator_ru_to_en)}
                            }
                        }
                    }
                }
            }
    else:
        if not is_exact_mode:
            return {
                "query": {
                    "bool": {
                        "must": {
                            "match": {"code": code}
                        },
                        "should": {
                            "match": {
                                "description_ru": {
                                    "query": search_string.translate(translator_en_to_ru),
                                    "fuzziness": "AUTO",
                                    "max_expansions": fuzziness_max_expansions
                                }
                            }
                        }
                    }
                }
            }
        else:
            return {
                "query": {
                    "bool": {
                        "must": {
                            "match": {"code": code}
                        },
                        "should": {
                            "match": {
                                "description_ru_exact": {"query": search_string.translate(translator_en_to_ru)}
                            }
                        }
                    }
                }
            }


# def get_okved_search_body():


def get_search_line_language(search_string):
    search_string_ru = search_string.translate(translator_en_to_ru)
    search_string_en = search_string.translate(translator_ru_to_en)
    output1, search_result1 = elastic_search(es, gtds_6_index_name,
                                             get_search_body(gtds_6_index_name, search_string_ru,
                                                             False, False, "ru"), False)
    output2, search_result2 = elastic_search(es, hs_index_name,
                                             get_search_body(hs_index_name, search_string_en,
                                                             False, False, "en"), False)
    if search_result1["total"]["value"] > 0 and search_result2["total"]["value"] > 0:
        if search_result1["max_score"] > search_result2["max_score"]:
            return "ru", search_string_ru, search_string_en
        else:
            return "en", search_string_ru, search_string_en
    elif search_result1["total"]["value"] > 0:
        return "ru", search_string_ru, search_string_en
    elif search_result2["total"]["value"] > 0:
        return "en", search_string_ru, search_string_en
    else:
        # здесь нужно сверяться с поиском по tnved
        # ПОМЕНЯТЬ ПОИСК С gtds_6 на new_gtds_10
        # вторая пристрелка, опять без учета tnved
        output1, search_result1 = elastic_search(es, gtds_6_index_name,
                                                 get_search_body(gtds_6_index_name, search_string_ru,
                                                                 False, False, "ru"), False)
        output2, search_result2 = elastic_search(es, gtds_6_index_name,
                                                 get_search_body(gtds_6_index_name, search_string_en,
                                                                 False, False, "en"), False)
        if search_result1["total"]["value"] > 0 and search_result2["total"]["value"] > 0:
            if search_result1["max_score"] > search_result2["max_score"]:
                return "ru", search_string_ru, search_string_en
            else:
                return "en", search_string_ru, search_string_en
        elif search_result1["total"]["value"] > 0:
            return "ru", search_string_ru, search_string_en
        elif search_result2["total"]["value"] > 0:
            return "en", search_string_ru, search_string_en
        else:
            # когда нигде ничего не нашлось
            return "ru", search_string_ru, search_string_en


def get_item_clicked_output(search_string, code):
    global es
    with closing(psycopg2.connect(dbname='adb', user='adb_admin',
                                  password='Aren@DB_admin', host='VM-CO-MDW-01.exportcenter.ru')) as conn:
        with conn.cursor() as cursor:

            language, search_string_ru, search_string_en = get_search_line_language(search_string)
            output_approx, search_result_approx = elastic_search(es, tnved_10_index_name,
                                                                 get_one_result_search_body(search_string, code,
                                                                                            False, language),
                                                                 False)
            output_exact, search_result_exact = elastic_search(es, tnved_10_index_name,
                                                               get_one_result_search_body(search_string, code,
                                                                                          True, language),
                                                               False)
            output, result = combine_one_index_search_results(tnved_10_index_name,
                                                              [search_result_approx, search_result_exact])

            hit_num = 0
            full_output = []
            values_list = []
            for code in result.keys():
                fields = result[code]
                values_list.append("('" + str(code) + "', " + str(fields[0]) + ")")
                hit_num += 1
            if hit_num > 0:
                cursor.execute("WITH cs(code, score) AS (VALUES " + ", ".join(values_list) + ")\n"
                               + "select hrh.code, hrh.description, cs.score from "
                                 '(select t1."ten-digits-code" as code, t1."description" as description '
                                 'from data_valut.h_russian_hscodes as t1 where t1.valid_till='
                                 '(select max(t2.valid_till) from data_valut.h_russian_hscodes as t2 where t2."hscode"=t1."hscode")'
                                 ") as hrh\nINNER JOIN cs on hrh.code=cs.code order by "
                                 "cs.score desc;")

                db_results = cursor.fetchall()
                hit_num = 0
                for db_result in db_results:
                    item_output = ""
                    item_output += "Показатель релевантности результата: " + str(
                        round(float(db_result[2]), 4)) + "\n"
                    # item_output += "Найден в индексах: " + ", ".join(db_result[2]) + "\n"
                    item_output += "Код ТНВЭД: " + str(db_result[0]) + "\n"
                    item_output += "Описание ТНВЭД: " + db_result[1] + "\n"
                    full_output.append(item_output)
                    hit_num += 1
                    if hit_num == 20:
                        break
            else:
                full_output.append("По запросу ничего не найдено")
            return full_output


def search_for_ui(search_string):
    global translator_en_to_ru
    global es, search_index_names
    status = 0
    if elastic_search(es, "mat", get_search_body("mat", search_string, False, False, "ru"), False)[1]["total"][
        "value"] > 0 or elastic_search(es, "mat",
                                       get_search_body("mat", search_string.translate(translator_en_to_ru), False,
                                                       False, "ru"), False)[1]["total"]["value"] > 0:
        # return 1, "", ""
        return [{"id": "-", "block": "-", "header": "Обнаружены нецензурные выражения", "url": "-",
                 "create_date": "-", "score_block": "-", "score_total": "-"}]
    else:
        # проверяем, перешли ли в режим поиска по коду (есть ли в строке 3 цифры подряд)
        curr_str = ""
        max_curr_str = ""
        for ch in search_string:
            if ch.isdigit():
                curr_str += ch
            else:
                if len(curr_str) > len(max_curr_str):
                    max_curr_str = curr_str
                curr_str = ""
        if len(curr_str) > len(max_curr_str):
            max_curr_str = curr_str
        is_code_search_mode = len(max_curr_str) >= 3
        if is_code_search_mode:
            status = 2
        # список выводов результатов поиска для разных индексов по отдельности
        output_list = []
        # список результатов поиска для разных индексов
        search_result_list = []
        # определяем язык в поисковой строке
        language = ""
        if not is_code_search_mode:
            language, search_string_ru, search_string_en = get_search_line_language(search_string)
        if language == "ru":
            search_index_names = [tnved_6_index_name, gtds_6_index_name]
        else:
            search_index_names = [tnved_6_index_name, gtds_6_index_name, hs_index_name]

        for search_index_name in search_index_names:
            if is_code_search_mode:
                output_code, search_result_code = elastic_search(es, search_index_name,
                                                                 get_search_body(search_index_name, max_curr_str,
                                                                                 is_code_search_mode, False,
                                                                                 language), is_code_search_mode)
                output_list.append(output_code)
                search_result_list.append(search_result_code)
            else:
                output_approx, search_result_approx = elastic_search(es, search_index_name,
                                                                     get_search_body(search_index_name,
                                                                                     search_string,
                                                                                     is_code_search_mode, False,
                                                                                     language),
                                                                     is_code_search_mode)
                output_exact, search_result_exact = elastic_search(es, search_index_name,
                                                                   get_search_body(search_index_name,
                                                                                   search_string,
                                                                                   is_code_search_mode,
                                                                                   True, language),
                                                                   is_code_search_mode)
                output, result = combine_one_index_search_results(search_index_name,
                                                                  [search_result_approx, search_result_exact])
                output_list.append(output)
                search_result_list.append(result)

        output_combo_for_ui = combine_multiple_index_search_results_for_ui(search_result_list)

        return output_combo_for_ui


def combine_multiple_index_search_results_for_ui(search_result_list):
    global search_index_names
    search_result_num = 0
    # словарь search_result: код - [score; описание]
    # словарь code_fields_dict: код - [score; описание; список с индексами, в которых код нашелся]
    code_fields_dict = {}
    for search_result in search_result_list:
        # предполагаем, что массив с результатами поисков заполнен в порядке имен индексов в search_index_names
        index_name = search_index_names[search_result_num]
        if index_name == tnved_6_index_name or index_name == tnved_10_index_name:
            for code in search_result.keys():
                if code not in code_fields_dict.keys():
                    code_fields_dict[code] = [
                        search_result[code][0] * index_name_boost_dict[index_name],
                        search_result[code][1],
                        [index_name]]
                else:
                    # увеличиваем score; заменяем описание; добавляем индекс в найденные
                    code_fields_dict[code] = [
                        code_fields_dict[code][0] + search_result[code][0] *
                        index_name_boost_dict[index_name],
                        search_result[code][1],
                        code_fields_dict[code][2] + [index_name]]
        elif index_name == gtds_6_index_name or index_name == gtds_10_index_name:
            for code in search_result.keys():
                if code not in code_fields_dict.keys():
                    code_fields_dict[code] = [
                        search_result[code][0] * index_name_boost_dict[index_name],
                        search_result[code][1],
                        [index_name]]
                else:
                    # увеличиваем score; оставляем старое описание; добавляем индекс в найденные
                    code_fields_dict[code] = [
                        code_fields_dict[code][0] + search_result[code][0] *
                        index_name_boost_dict[index_name],
                        code_fields_dict[code][1],
                        code_fields_dict[code][2] + [index_name]]
        elif index_name == hs_index_name:
            for code in search_result.keys():
                if code not in code_fields_dict.keys():
                    code_fields_dict[code] = [
                        search_result[code][0] * index_name_boost_dict[index_name],
                        search_result[code][1],
                        [index_name]]
                else:
                    # увеличиваем score; оставляем старое описание; добавляем индекс в найденные
                    code_fields_dict[code] = [
                        code_fields_dict[code][0] + search_result[code][0] *
                        index_name_boost_dict[index_name],
                        code_fields_dict[code][1],
                        code_fields_dict[code][2] + [index_name]]

        search_result_num += 1

    sorted_results = sorted(code_fields_dict.items(), key=lambda x: x[1][0], reverse=True)

    # max_score = 1
    # hit_num = 0
    # full_output = []
    # for code, fields in sorted_results:
    #     hit_num += 1
    #     item_output = ""
    #     item_output += "Показатель релевантности результата: " + str(
    #         round(float(fields[0]) / max_score, 4)) + "\n"
    #     item_output += "Найден в индексах: " + ", ".join(fields[2]) + "\n"
    #     item_output += "Код ТНВЭД: " + str(code) + "\n"
    #     item_output += "Описание ТНВЭД: " + fields[1] + "\n"
    #     full_output.append(item_output)
    # if hit_num == 0:
    #     full_output.append("По запросу ничего не найдено")

    hit_num = 0
    full_output = []
    values_list = []
    for code, fields in sorted_results:
        values_list.append("('" + str(code) + "', " + str(fields[0]) + ")")
        hit_num += 1
    if hit_num > 0:
        with closing(psycopg2.connect(dbname='adb', user='adb_admin',
                                      password='Aren@DB_admin', host='VM-CO-MDW-01.exportcenter.ru')) as conn:
            with conn.cursor() as cursor:
                cursor.execute("WITH cs(code, score) AS (VALUES " + ", ".join(values_list) + ")\n"
                               + "select hrh.id as code, hrh.name as description, cs.score from (select distinct on (id) * from "
                                 "data_valut.h_russian_hscodes_6_solo) as hrh\nINNER JOIN cs on hrh.id=cs.code order by "
                                 "cs.score desc;")

                db_results = cursor.fetchall()
                hit_num = 0
                for db_result in db_results:
                    item = {"id": str(db_result[0]), "block": "-", "header": db_result[1], "url": "-",
                            "create_date": "-", "score_block": "-", "score_total": "-"}

                    # item_output += "Показатель релевантности результата: " + str(round(float(db_result[2]), 4)) + "\n"
                    # item_output += "Найден в индексах: " + ", ".join(db_result[2]) + "\n"
                    full_output.append(item)
                    hit_num += 1
                    if hit_num == 20:
                        break
    else:
        full_output.append({"id": "-", "block": "-", "header": "По запросу ничего не найдено", "url": "-",
                            "create_date": "-", "score_block": "-", "score_total": "-"})

    return full_output


def search(search_string):
    global translator_en_to_ru
    global es, search_index_names
    status = 0
    if elastic_search(es, "mat", get_search_body("mat", search_string, False, False, "ru"), False)[1]["total"][
        "value"] > 0 or elastic_search(es, "mat",
                                       get_search_body("mat", search_string.translate(translator_en_to_ru), False,
                                                       False, "ru"), False)[1]["total"]["value"] > 0:
        return 1, "", ""
    else:
        # проверяем, перешли ли в режим поиска по коду (есть ли в строке 3 цифры подряд)
        curr_str = ""
        max_curr_str = ""
        for ch in search_string:
            if ch.isdigit():
                curr_str += ch
            else:
                if len(curr_str) > len(max_curr_str):
                    max_curr_str = curr_str
                curr_str = ""
        if len(curr_str) > len(max_curr_str):
            max_curr_str = curr_str
        is_code_search_mode = len(max_curr_str) >= 3
        if is_code_search_mode:
            status = 2
        # список выводов результатов поиска для разных индексов по отдельности
        output_list = []
        # список результатов поиска для разных индексов
        search_result_list = []
        # определяем язык в поисковой строке
        language = ""
        if not is_code_search_mode:
            language, search_string_ru, search_string_en = get_search_line_language(search_string)
        if language == "ru":
            search_index_names = [tnved_6_index_name, gtds_6_index_name]
        else:
            search_index_names = [tnved_6_index_name, gtds_6_index_name, hs_index_name]

        for search_index_name in search_index_names:
            if is_code_search_mode:
                output_code, search_result_code = elastic_search(es, search_index_name,
                                                                 get_search_body(search_index_name, max_curr_str,
                                                                                 is_code_search_mode, False,
                                                                                 language), is_code_search_mode)
                output_list.append(output_code)
                search_result_list.append(search_result_code)
            else:
                output_approx, search_result_approx = elastic_search(es, search_index_name,
                                                                     get_search_body(search_index_name,
                                                                                     search_string,
                                                                                     is_code_search_mode, False,
                                                                                     language),
                                                                     is_code_search_mode)
                output_exact, search_result_exact = elastic_search(es, search_index_name,
                                                                   get_search_body(search_index_name,
                                                                                   search_string,
                                                                                   is_code_search_mode,
                                                                                   True, language),
                                                                   is_code_search_mode)
                output, result = combine_one_index_search_results(search_index_name,
                                                                  [search_result_approx, search_result_exact])
                output_list.append(output)
                search_result_list.append(result)

        output_combo = combine_multiple_index_search_results(search_result_list)
        return status, output_list, output_combo


def elastic_search(es, index_name, search_body, is_code_search_mode):
    es_result = es.search(index=index_name, body=search_body)
    code_fields_dict = {}
    # max_score = res["hits"]["max_score"]
    max_score = 1
    hit_num = 0
    output = ""
    output += "<" + index_name + ">\n\n"
    if index_name != "mat" and is_code_search_mode:
        for hit in es_result['hits']['hits']:
            source = hit["_source"]

            output += "Показатель релевантности результата: " + str(round(float(hit["_score"]) / max_score, 4)) + "\n"
            output += "Код ТНВЭД: " + str(hit["_source"]["code"]) + "\n"
            if index_name == hs_index_name:
                output += "Описание ТНВЭД: " + hit["_source"]["description_en"] + "\n\n\n"
                code_fields_dict[source["code"]] = [
                    hit["_score"],
                    source["description_en"]]
            else:
                output += "Описание ТНВЭД: " + hit["_source"]["description_en"] + "\n\n\n"
                code_fields_dict[source["code"]] = [
                    hit["_score"],
                    source["description_en"]]
            hit_num += 1
            if hit_num == 10:
                break

        if hit_num == 0:
            output += "По запросу ничего не найдено" + "\n\n\n"
        return output, code_fields_dict
    if es_result["hits"]["total"]["value"] == 0:
        output += "По запросу ничего не найдено" + "\n\n\n"
    return output, es_result['hits']


# объединение результатов точного и приближенного поиска в одном индексе
def combine_one_index_search_results(index_name, search_result_list):
    global one_index_search_results_boost_list
    search_result_num = 0
    # словарь: код - [score; описание; список с индексами, в которых код нашелся]
    code_fields_dict = {}
    for search_result in search_result_list:
        if index_name == tnved_6_index_name or index_name == tnved_10_index_name:
            for doc_num in range(len(search_result["hits"])):
                source = search_result["hits"][doc_num]["_source"]
                if source["code"] not in code_fields_dict.keys():
                    code_fields_dict[source["code"]] = [
                        search_result["hits"][doc_num]["_score"] * one_index_search_results_boost_list[
                            search_result_num],
                        source["description_ru"]]
                else:
                    # увеличиваем score; заменяем описание; добавляем индекс в найденные
                    code_fields_dict[source["code"]] = [
                        # code_fields_dict[source["code"]][0] + search_result["hits"][doc_num]["_score"] * one_index_search_results_boost_list[search_result_num],
                        code_fields_dict[source["code"]][0] * one_index_search_results_boost_list[search_result_num],
                        source["description_ru"]]
        elif index_name == gtds_6_index_name or index_name == gtds_10_index_name:
            for doc_num in range(len(search_result["hits"])):
                source = search_result["hits"][doc_num]["_source"]
                if source["code"] not in code_fields_dict.keys():
                    code_fields_dict[source["code"]] = [
                        search_result["hits"][doc_num]["_score"] * one_index_search_results_boost_list[
                            search_result_num] *
                        (1 + float(source["freq"]) / (2 * float(source["freq_max"]))),
                        source["description_ru"]]
                else:
                    # увеличиваем score; оставляем старое описание; добавляем индекс в найденные
                    code_fields_dict[source["code"]] = [
                        # code_fields_dict[source["code"]][0] + search_result["hits"][doc_num]["_score"] *
                        code_fields_dict[source["code"]][0] *
                        one_index_search_results_boost_list[search_result_num] * (
                                1 + float(source["freq"]) / (2 * float(source["freq_max"]))),
                        code_fields_dict[source["code"]][1]]
        elif index_name == hs_index_name:
            for doc_num in range(len(search_result["hits"])):
                source = search_result["hits"][doc_num]["_source"]
                if source["code"] not in code_fields_dict.keys():
                    code_fields_dict[source["code"]] = [
                        search_result["hits"][doc_num]["_score"] * one_index_search_results_boost_list[
                            search_result_num],
                        source["description_en"]]
                else:
                    # увеличиваем score; оставляем старое описание; добавляем индекс в найденные
                    code_fields_dict[source["code"]] = [
                        # code_fields_dict[source["code"]][0] + search_result["hits"][doc_num]["_score"] *
                        code_fields_dict[source["code"]][0] *
                        one_index_search_results_boost_list[search_result_num],
                        code_fields_dict[source["code"]][1]]

        search_result_num += 1

    max_score = 1
    hit_num = 0
    output = "<" + index_name + ">\n\n"
    # сортируем результаты сведения по убыванию релевантности
    sorted_results = sorted(code_fields_dict.items(), key=lambda x: x[1][0], reverse=True)
    for code, fields in sorted_results:
        output += "Показатель релевантности результата: " + str(
            round(float(fields[0]) / max_score, 4)) + "\n"
        output += "Код ТНВЭД: " + str(code) + "\n"
        output += "Описание ТНВЭД: " + fields[1] + "\n\n\n"
        hit_num += 1
        if hit_num == 10:
            break

    if hit_num == 0:
        output += "По запросу ничего не найдено" + "\n\n\n"
    return output, code_fields_dict


# объединение результатов поисков в нескольких индексах
def combine_multiple_index_search_results(search_result_list):
    global search_index_names
    search_result_num = 0
    # словарь search_result: код - [score; описание]
    # словарь code_fields_dict: код - [score; описание; список с индексами, в которых код нашелся]
    code_fields_dict = {}
    for search_result in search_result_list:
        # предполагаем, что массив с результатами поисков заполнен в порядке имен индексов в search_index_names
        index_name = search_index_names[search_result_num]
        if index_name == tnved_6_index_name or index_name == tnved_10_index_name:
            for code in search_result.keys():
                if code not in code_fields_dict.keys():
                    code_fields_dict[code] = [
                        search_result[code][0] * index_name_boost_dict[index_name],
                        search_result[code][1],
                        [index_name]]
                else:
                    # увеличиваем score; заменяем описание; добавляем индекс в найденные
                    code_fields_dict[code] = [
                        code_fields_dict[code][0] + search_result[code][0] *
                        index_name_boost_dict[index_name],
                        search_result[code][1],
                        code_fields_dict[code][2] + [index_name]]
        elif index_name == gtds_6_index_name or index_name == gtds_10_index_name:
            for code in search_result.keys():
                if code not in code_fields_dict.keys():
                    code_fields_dict[code] = [
                        search_result[code][0] * index_name_boost_dict[index_name],
                        search_result[code][1],
                        [index_name]]
                else:
                    # увеличиваем score; оставляем старое описание; добавляем индекс в найденные
                    code_fields_dict[code] = [
                        code_fields_dict[code][0] + search_result[code][0] *
                        index_name_boost_dict[index_name],
                        code_fields_dict[code][1],
                        code_fields_dict[code][2] + [index_name]]
        elif index_name == hs_index_name:
            for code in search_result.keys():
                if code not in code_fields_dict.keys():
                    code_fields_dict[code] = [
                        search_result[code][0] * index_name_boost_dict[index_name],
                        search_result[code][1],
                        [index_name]]
                else:
                    # увеличиваем score; оставляем старое описание; добавляем индекс в найденные
                    code_fields_dict[code] = [
                        code_fields_dict[code][0] + search_result[code][0] *
                        index_name_boost_dict[index_name],
                        code_fields_dict[code][1],
                        code_fields_dict[code][2] + [index_name]]

        search_result_num += 1

    sorted_results = sorted(code_fields_dict.items(), key=lambda x: x[1][0], reverse=True)

    # max_score = 1
    # hit_num = 0
    # full_output = []
    # for code, fields in sorted_results:
    #     hit_num += 1
    #     item_output = ""
    #     item_output += "Показатель релевантности результата: " + str(
    #         round(float(fields[0]) / max_score, 4)) + "\n"
    #     item_output += "Найден в индексах: " + ", ".join(fields[2]) + "\n"
    #     item_output += "Код ТНВЭД: " + str(code) + "\n"
    #     item_output += "Описание ТНВЭД: " + fields[1] + "\n"
    #     full_output.append(item_output)
    # if hit_num == 0:
    #     full_output.append("По запросу ничего не найдено")

    hit_num = 0
    full_output = []
    values_list = []
    for code, fields in sorted_results:
        values_list.append("('" + str(code) + "', " + str(fields[0]) + ")")
        hit_num += 1
    if hit_num > 0:
        with closing(psycopg2.connect(dbname='adb', user='adb_admin',
                                      password='Aren@DB_admin', host='VM-CO-MDW-01.exportcenter.ru')) as conn:
            with conn.cursor() as cursor:
                cursor.execute("WITH cs(code, score) AS (VALUES " + ", ".join(values_list) + ")\n"
                               + "select hrh.id as code, hrh.name as description, cs.score from (select distinct on (id) * from "
                                 "data_valut.h_russian_hscodes_6_solo) as hrh\nINNER JOIN cs on hrh.id=cs.code order by "
                                 "cs.score desc;")

                db_results = cursor.fetchall()
                hit_num = 0
                for db_result in db_results:
                    item_output = ""
                    item_output += "Показатель релевантности результата: " + str(round(float(db_result[2]), 4)) + "\n"
                    # item_output += "Найден в индексах: " + ", ".join(db_result[2]) + "\n"
                    item_output += "Код ТНВЭД: " + str(db_result[0]) + "\n"
                    item_output += "Описание ТНВЭД: " + db_result[1] + "\n"
                    full_output.append(item_output)
                    hit_num += 1
                    if hit_num == 20:
                        break
    else:
        full_output.append("По запросу ничего не найдено")

    return full_output