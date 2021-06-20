import re


class RegexElement:
    regex = ''
    name = ''

    def __init__(self, name, regex):
        assert type(regex) == str
        self.regex = regex
        self.name = name

    def search(self, target):
        if type(target) == str:
            return self._search_string(target)
        elif type(target) == list:
            return [self._search_string(i) for i in target]
        else:
            raise TypeError(f'Expected type list or str: {type(target)}')

    def _search_string(self, s):
        return True if re.search(self.regex, s, re.MULTILINE) else False

    def __str__(self):
        return f'Regex for search {self.name}'


class RegexSearch:
    regex_elements = dict()

    def __init__(self, regex: dict):
        assert type(regex) == dict
        for key, value in regex.items():
            self.regex_elements[key] = RegexElement(key, value)

    def search_all(self, target):
        if type(target) == str:
            return self._search_str(target)
        elif type(target) == list:
            return [self._search_str(i) for i in target]
        else:
            raise TypeError(f'Expected type list or str: {type(target)}')

    def _search_str(self, s):
        answer = dict()
        for key, element in self.regex_elements.items():
            is_find = element.search(s)
            answer[key] = is_find
        return answer

    def __iter__(self):
        return self.regex_elements.keys()

    def __getitem__(self, item):
        return self.regex_elements[item]


regex_dict = {
    'usermail': r"^[a-zA-Z0-9_]+([a-zA-Z0-9_.-]+)?[a-zA-Z0-9_]+\@[a-zA-Z0-9]([a-zA-Z0-9._-]+)?\.[a-zA-Z]+?$",
    'ipaddress': r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3})|((([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])))",
    'user_ID': r'[\W]+',
    'username': r"^[ \ta-zA-ZА-Яа-я0-9_-]{3,16}$",
    'userpass_plain': r'^[ \t\Wa-zA-ZА-Яа-я0-9_-]{6,18}$',
}
# Email regex
# Адрес начинается с любого из символов a-z, A-Z, цифр 0-9 или подчеркивания _
# минимум от 1 символа. " ^[a-zA-Z0-9_]+ "
# Потом идет необязательная часть, которая может содержать точку или дефис
# кроме остальных символов " ([a-zA-Z0-9_.-]+)? " Скобки означают группу, анак вопроса
# говорит, что группа может встретиться 0 или 1 раз
# Оканчивается левая часть адреса любыми символами из списка " a-z, A-Z, 0-9, _ "
# Потом собачка
# Справа часть начинается с любого из символов " a-z, A-Z, 0-9 "минимум 1 символа,
# потом какие-то буквы или цифры или точка или _ -, и в конце точка и что-то из a-z, A-Z

rs = RegexSearch(regex_dict)
#
# targets = ['user123', 'password123Pass', 'mail@mail.ru']
#
# # Список на что похожа строка
# all_result_dim_1 = rs.search_all(targets[0])  # [0, 0, ... 1]
#
# # Список со списками на что похожи слова
# all_result_dim_2 = rs.search_all(targets)  # [[0, 1, ... 0], [0, 0, ... 1], [1, 0, ... 0]]
#
# # Похож ли элемент на майл
# result_for_element = rs['email'].search(targets[0])  # 0
#
# # Список истинности похожих на майл
# result_for_elements = rs['email'].search(targets)  # [0, 0, 1]
#
#
# print(all_result_dim_1)
# print(all_result_dim_2)
# print(result_for_element)
# print(result_for_elements)
