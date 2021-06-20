import math
import time

from chardet.universaldetector import UniversalDetector
from collections import Counter

from rich.highlighter import RegexHighlighter
from rich.progress import Progress, track
from rich.prompt import Prompt
from rich.text import Text
from rich.theme import Theme

from Regex import regex_dict, rs
from hash_identifer import identify_hashes
import os
import shutil
import pandas
from pathlib import Path
import re
from rich.console import Console

import subprocess
import sys
import csv

maxInt = sys.maxsize
while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)


class DelimiterHighlighter(RegexHighlighter):
    base_style = "text."
    highlights = [r"(?P<all>.)", r"(?P<delimiter>[,:;|])"]


theme = Theme({"text.delimiter": "bold red", "text.all": "yellow"})
console = Console()
console_for_show = Console(highlighter=DelimiterHighlighter(), theme=theme)
PD = os.environ['PARSING_DISK_NAME']


def get_encoding_file(path):
    detector = UniversalDetector()
    with open(path, 'rb') as fh:
        for line in fh.readlines(10000):
            detector.feed(line)
            if detector.done:
                break
        detector.close()
    return detector.result['encoding']


def get_plain_files(files_paths):
    """
    Возвращает бд с открытыми паролями.
    Например:
    [
        "name_hash.txt",
        "name_not_found.txt",
        "name_result.txt",
    ]
    Возвратит ['name_result.txt']
    """

    # Какие слова нужно искать
    triggers = ['result', 'decrypted', 'no hash', 'no_hash', 'nohash', 'nothash']

    res = []

    for fp in files_paths:
        file_name = fp.name
        if 'result(hex)' in file_name.lower():
            continue
        for trigger in triggers:
            if trigger in file_name.lower():
                res.append(fp)
    return res if res else files_paths


def get_combo_command(**kwargs):
    data = kwargs
    data['name'] = data['name'].replace("'", '')
    data['source'] = data['source'].replace("'", '')

    cmd = f"python3 main.py" \
          f" --user {data['user']}" \
          f" --password {data['password']}" \
          f" --database db_{data['user']}" \
          f" --date {data['date']}" \
          f" --delimiter" \
          f" '{data['delimiter']}'" \
          f" --name '{data['name']}'" \
          f" --source '{data['source']}'" \
          f" --type combo" \
          f" --src '../files/{data['file'].name}'" \
          f" --colsname '{','.join(data['cols'])}'" \
          f" --quotes\n"
    return cmd


def get_db_command(**kwargs):
    data = kwargs
    data['name'] = data['name'].replace("'", '')
    data['source'] = data['source'].replace("'", '')

    cmd = f"python3 main.py" \
          f" --date {data['date']}" \
          f" --delimiter" \
          f" '{data['delimiter']}'" \
          f" --name '{data['name']}'" \
          f" --source '{data['source']}'" \
          f" --type database" \
          f" --user {data['user']}" \
          f" --password {data['password']}" \
          f" --database db_{data['user']}" \
          f" --src '../files/{data['file'].name}'" \
          f" --colsname '{','.join(data['cols'])}'" \
          f" --quotes\n"
    if 'hash' in data['cols']:
        hash_type = manager.get_type_hash(str(data['file'].absolute()))
        if hash_type:
            cmd = cmd.replace('\n', '')
            cmd += f" --algorithm '{hash_type}'\n"
    return cmd


class HashManager:

    def get_type_hash(self, path):
        m = self.parse(path)
        occurence_count = Counter(m.values())
        if not occurence_count.values():
            return None
        return occurence_count.most_common(1)[0][0]

    def hash_type(self, word):
        algorithms = identify_hashes(word)
        return algorithms[0] if algorithms else None

    def parse(self, file):
        path = Path(file)
        if not path.is_file():
            raise TypeError("unknown path")

        hash_arr = {}
        c = 0
        with open(file, "r", encoding=get_encoding_file(file), errors='ignore') as f:
            for line in f.readlines():
                c += 1
                if c > 10000:
                    break
                for word in re.findall(r"[^\s:,]+", line):
                    hash = self.hash_type(word)
                    if hash:
                        hash_arr[word] = hash

        return hash_arr


manager = HashManager()


def show_file(file: Path):
    console_for_show.print(f'[bold magenta]{file.absolute()}')
    console_for_show.print("[magenta]" + '-' * 200, overflow='crop')
    with file.open('r', encoding='utf-8') as f:
        for line in fix_nulls(f, hit=15):
            line_to_show = line[:3000] if len(line) > 3000 else line
            console_for_show.print(line_to_show, end='', )
    print('\n')


def get_keys(inp):
    """
    :param inp: "1=usermail, 3=username"
    :return: Порядок для бд, ключи для fix.py
    """
    args_inp = inp.split(',')
    key_res = []
    for arg in args_inp:
        arg = arg.strip()
        data_key = arg.split('=')
        key_res.append(data_key[1])
    colsname_plain = key_res[::]
    if 'user_additional_info' in colsname_plain:
        while colsname_plain.count('user_additional_info') > 0:
            colsname_plain.remove('user_additional_info')
        colsname_plain.append('user_additional_info')
    keys = [tuple(i.split('=')) for i in args_inp]
    return keys, colsname_plain


def write_to_complete(dir, type):
    with open(os.path.join('C:\\', 'Source', type, 'parsing_complete.txt'), 'a', encoding='utf-8') as f:
        f.write("\n" + str(dir.absolute()))


def write_to_passed_dirs(dir, type):
    with open(os.path.join('C:\\', 'Source', type, 'passed_dirs.txt'), 'a', encoding='utf-8') as f:
        f.write("\n" + str(dir.absolute()))


def move_to(dir, type, destination):
    PD = str(os.environ['PARSING_DISK_NAME'])
    dir = str(dir)
    line_source = dir.replace('C:\\Source', f'{PD}:\\Source')
    line_move = line_source.replace(f'{PD}:\\Source', f'{PD}:\\' + destination.capitalize())
    if type == 'combo':
        path_source = Path(os.path.join(*Path(line_source).parts[:4]))
        path_move = Path(os.path.join(*Path(line_move).parts[:4]))
        shutil.move(str(path_source), str(path_move))
    else:
        path_source = Path(os.path.join(*Path(line_source).parts[:5]))
        path_move = Path(os.path.join(*Path(line_move).parts[:5]))
        if not Path(os.path.join(*path_move.parts[:4])).exists():
            Path(os.path.join(*path_move.parts[:4])).mkdir()
        shutil.move(str(path_source), str(path_move))


def csv_write_2(path: Path, keys: tuple, colsnames, delimiter: str, skip: int):
    new_delimiter = ';' if delimiter == '\t' else delimiter
    delete_values_list = ['NULL', 'null', '<blank>']  # Значения для замены на пустоту

    # new_path = fix_file(path)  # файл без ошибок чтения
    rewrite_path = Path(os.path.splitext(str(path.absolute()))[0] + '_rewrite.txt')
    file_for_reading = path.open('r', newline="", encoding='utf-8')
    file_for_writing = rewrite_path.open('w', encoding='utf-8')

    fixer = fix_nulls(file_for_reading)

    for _ in range(skip):
        try:
            next(fixer)
        except StopIteration:
            pass

    reader = csv.reader(fixer, delimiter=delimiter, quoting=csv.QUOTE_NONE)

    with console.status('[bold blue]Парсинг файла...', spinner='point', spinner_style="bold blue") as status:
        for line in reader:
            main = []  # Главный список
            add_info = []  # доп инфа
            if len(line) < len(keys):
                continue

            for i, key in keys:
                i = int(i) - 1
                try:
                    line[i] = line[i].strip(' "\'')
                except IndexError:
                    break
                if key in ['userpass_plain', 'hash']:
                    try:
                        line[i] = line[i].split()[0]
                    except IndexError:
                        pass

                if key == "user_additional_info":
                    add_info.append(cleaner(line[i], delete_values_list, new_delimiter))
                else:
                    main.append(cleaner(line[i], delete_values_list, new_delimiter))
            else:
                if add_info:
                    main.append('|'.join(add_info))
                main_string = f'{new_delimiter}'.join(main)
                file_for_writing.write(main_string + '\n')

    file_for_reading.close()
    file_for_writing.close()
    return rewrite_path


def is_simple_file(r, list_string):
    reg = r
    answer = [re.search(reg, s, re.IGNORECASE) for s in list_string]
    return any(answer)


def cleaner(s: str, values: list, delimiter=None):
    line = s
    for sfx in values:
        line = line.replace(sfx, "")
    if delimiter and delimiter in line:
        line = f'"{line}"'
    return line


def validate_field(s, key):
    if not s:
        return False
    value = s.strip(' \t')
    print(s, value)
    if key == 'hash':
        return bool(manager.hash_type(value))
    if key not in regex_dict:
        return True
    return bool(rs[key].search(value))


def check_file_on_wrapper(path, tag, delimiter):
    if not delimiter:
        return False
    with open(path, encoding=get_encoding_file(path), errors='ignore') as f:
        if tag == 'anonymous':
            for _ in range(5):
                if "1:Anonymous:::" in f.readline():
                    return True
        if tag == 'login:pass':
            using_password = set()
            using_password_count = 0
            n = 100
            err = 0
            valid_usermail_string_count = 0
            valid_username_string_count = 0
            for _ in range(n):
                s = f.readline().strip()
                if not s:
                    continue
                s = s.split(delimiter)
                if len(s) != 2:
                    err += 1
                    continue
                login, password = s[0], s[1].replace('\n', '')
                if not password or not (rs['userpass_plain'].search(password) or manager.hash_type(password)):
                    err += 1
                    continue
                if password in using_password:
                    using_password_count += 1
                    if using_password_count > 0.3 * n:
                        return False
                using_password.add(password)
                if rs['usermail'].search(login):
                    valid_usermail_string_count += 1
                elif rs['username'].search(login):
                    valid_username_string_count += 1
                else:
                    err += 1
            if valid_usermail_string_count > err + valid_username_string_count:
                return 'usermail'
            if valid_username_string_count > err + valid_usermail_string_count:
                return 'username'
        if tag == 'uid_usrn_ip_usrm_hash_salt':
            keys_name_regex_tab = r"userid\s+username\s+ipaddress\s+email\s+token\s+secret"
            # keys_name_regex_colon = r".*:.*:.*:.*:.*:.*[^:]$"
            keys_name_find = False
            err = 0
            for i in range(20):
                s = f.readline()
                if re.search(keys_name_regex_tab, s) and len(s.split('\t')) == 6:
                    return '\t', i + 1


def xlsx_to_txt(path):
    name = os.path.splitext(path)[0] + '.txt'
    with open(name, 'w', encoding=get_encoding_file(path), errors='ignore') as file:
        pandas.read_excel(path).to_csv(file, index=False)
    return name


def fix_nulls(f, hit=math.inf):
    if f.mode == 'rb':
        count = 0
        while count <= hit:
            try:
                s = f.readline()
                if not s:
                    break
                line = s.replace(b'\0', b'').replace(b'\r', b'')
                line = line.decode('utf-8')
                # print(line)
            except UnicodeDecodeError as e:
                # print(e)
                continue
            if line == '' or line == '\n':
                continue
            count += 1
            yield line
    elif f.mode == 'r':
        count = 0
        while count <= hit:
            try:
                s = f.readline()
                if not s:
                    break
                line = s.replace('\0', '')
                # print(line)
            except UnicodeDecodeError as e:
                continue
            if line == '' or line == '\n':
                continue
            count += 1
            yield line


def get_source_from_readme(readme: Path):
    source = None
    for arg in fix_nulls(readme.open()):

        if arg.replace("\n", "").startswith('http') or arg.replace("\n", "") == "OLD DATABASES":
            source = arg.replace("\n", "")
            break
        if 'https://' in arg.replace("\n", ""):
            source = 'https://' + arg.replace("\n", "").split('https://', 1)[-1]
            break
        if 'http://' in arg.replace("\n", ""):
            source = 'http://' + arg.replace("\n", "").split('http://', 1)[-1]
            break
    if not source:
        console.print("[yellow]Не удалось найти source в readme!")
        subprocess.run(f"notepad {readme.absolute()}")
        source = Prompt.ask('Source')
    return source


def get_list_dirs_for_pass(path):
    passed_dirs = Path(os.path.join(path, 'passed_dirs.txt')).open(encoding='utf-8').readlines()
    passed_dirs = list(map(lambda x: x.strip(), passed_dirs))

    parsing_complete = Path(os.path.join(path, 'parsing_complete.txt')).open(encoding='utf-8').readlines()
    parsing_complete = list(map(lambda x: x.replace('\n', ''), parsing_complete))

    return parsing_complete, passed_dirs


def fix_file(path: Path):
    new_path = Path(os.path.splitext(str(path.absolute()))[0] + '_gotovo.txt')
    new_file = new_path.open('w', encoding='utf-8')
    with console.status('[bold blue]Ремонт файла...') as status:
        for i, s in enumerate(fix_nulls(path.open('r', encoding='utf-8'))):
            new_file.write(s)

            # if i % (abs(len(str(i)) - 2) + 1) == 0:
            #     status.update(f'[bold blue]Ремонт файла, обработано {i} строк')
    new_file.close()
    return new_path


def get_delimiter(path: Path):
    """
    Получение разделителя
    :param path: путь до csv
    :return: dialect
    """
    f = path.open('r', encoding='utf-8')
    try:
        return csv.Sniffer().sniff(''.join([i for i in fix_nulls(f, hit=20)]), delimiters=',:;\t').delimiter
    except csv.Error:
        return None


def get_all_files_in_dir(path_to_dir):
    # Сбор всех файлов с папки
    all_files: list[Path] = []
    for root, dirs, files in os.walk(path_to_dir):
        files = list(filter(lambda x: not x.startswith('_')
                                      and not x.endswith('_rewrite.txt')
                                      and not x.lower() == 'readme.txt'
                                      and not x.endswith('_rewrite_hashes.txt')
                                      and not x.endswith('_gotovo.txt'), files))
        path_files: list[Path] = [Path(os.path.join(root, f)) for f in files]

        clean_files = []
        for p in path_files:
            path = p
            if p.name.endswith('.xls') or p.name.endswith('.xlsx'):
                # path = Path(xlsx_to_txt(p.absolute()))
                if Prompt.ask(f'[yellow]Встречен "{p.name}" файл,'
                              f' создайте файл "{os.path.splitext(p.name)[0]}.txt" и нажмите "y" или "n" чтобы пропустить',
                              choices=['y', 'n']) == 'y':
                    path = Path(f'{os.path.splitext(str(p.absolute()))[0]}.txt')
                    while not path.exists():
                        Prompt.ask("\tФайл не обнаружен, проверьте ещё раз.")

                else:
                    continue
            clean_files.append(path)

        all_files += clean_files
    return all_files


def parsing_file(files):
    pass


def fix_row(gen, delimiter):
    """ Экранирование крайних кавычек перед разделителем в строке,
        дабы csv.reader не думал, что следующая строка относится к этой... балбес"""
    for line in gen:
        # yield re.sub(delimiter + r'["]([^"]+$)', delimiter + r"\"\1", line)
        yield re.sub(delimiter + r'["]([^"]+$)', delimiter + r'\"\1', line)
