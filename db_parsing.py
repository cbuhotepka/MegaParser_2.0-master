import os
import re
import subprocess
import time
from pathlib import Path
from typing import Generator

from rich.console import Console
from rich.prompt import Prompt, IntPrompt

import utils
from MegaParser import DataBaseDir, AbstractDataBaseDir

user = os.environ.get('USER_NAME')
password = os.environ.get('USER_PASSWORD')
PD = os.environ['PARSING_DISK_NAME']
console = Console()

def start(auto_parse):
    start_path = os.path.join('C:\\', 'Source', 'db')
    for p in ['parsing_complete.txt', 'passed_dirs.txt']:
        Path(os.path.join(start_path, p)).touch()
    iter_dirs = iter_for_db(start_path)
    parse(iter_dirs, auto_parse)


def iter_for_db(start_path):
    parsing_complete, passed_dirs = utils.get_list_dirs_for_pass(start_path)

    for root_name in os.listdir(start_path):
        if not os.path.isdir(os.path.join(start_path, root_name)):
            continue
        for item_name in os.listdir(os.path.join(start_path, root_name)):
            item = Path(os.path.join(start_path, root_name, item_name))
            if str(item.absolute()) in parsing_complete:
                console.print(f'[bold green]{item.absolute()}')
                continue
            elif str(item.absolute()) in passed_dirs:
                console.print(f'[bold yellow]{item.absolute()}')
                continue
            if item.is_dir():
                yield item
            else:
                continue


def parse(all_dirs: Generator, auto_parse):
    # Итерируемся по каталогам
    for dir in all_dirs:

        # (1) - Инициализация папки
        path_to_dir = str(dir.absolute())

        all_files = utils.get_all_files_in_dir(path_to_dir)
        if not all_files:
            console.print(f"[bold red]{path_to_dir} - Папка пуста")
            utils.write_to_passed_dirs(dir, 'db')
            continue
        console.print(f"[bold cyan]{path_to_dir}")
        name, date, source = get_meta_for_db(dir)
        dir_as_db = AbstractDataBaseDir(path_to_dir, name, date, source)

        # (2) - Процесс парсинга:

        # Команда для fix.py
        command = open(os.path.join(path_to_dir, '_command_.txt'), 'w', encoding='utf-8')


        all_files = utils.get_plain_files(all_files)

        # Парсинг файлов
        is_pass = []
        for file in all_files:

            skip = 0

            # Показ первых строк
            utils.show_file(file)
            delimiter = utils.get_delimiter(file)

            # Поиск на шаблоны для автопарсинга
            if auto_parse and (utils.is_simple_file(r'Num.*Pass', [file.name, dir.name])):
                keys, colsname_plain = utils.get_keys('1=tel, 2=userpass_plain')

                console.print('[cyan]' + 'Автопарсинг tel userpass_plain')
                console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')
            elif auto_parse and (utils.check_file_on_wrapper(file, 'anonymous', delimiter)):
                keys, colsname_plain = utils.get_keys('2=username, 3=ipaddress, 4=usermail, 5=hash')

                console.print('[cyan]' + f'Автопарсинг username ipaddress usermail hash')
                console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')
            elif auto_parse and (login := utils.check_file_on_wrapper(file, 'login:pass', delimiter)):
                keys, colsname_plain = utils.get_keys(f'1={login}, 2=userpass_plain')

                console.print('[cyan]' + f'Автопарсинг {login} userpass_plain')
                console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')
            elif auto_parse and (ans := utils.check_file_on_wrapper(file, 'uid_usrn_ip_usrm_hash_salt', delimiter)):
                keys, colsname_plain = utils.get_keys('1=user_ID, 2=username, 3=ipaddress, 4=usermail, 5=hash, 6=salt')
                skip = ans[1]

                console.print('[cyan]' + f'Автопарсинг username ipaddress usermail hash')
                console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')
            else:
                if not delimiter:
                    console.print(f'[magenta]Разделитель[/magenta]: [red]Отсутствует![/red]')
                else:
                    console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')

                # Действия
                while True:
                    decree = Prompt.ask(f"[green]Если все ОК нажмите Enter", choices=['p', 'l', 'o', 'n', 'd', 'e', 't'],
                        default='')
                    if decree == 'p':
                        # Пропустить все оставшееся
                        is_pass.append(True)
                        break
                    elif decree == 'e':
                        # Перенести папку в ERROR
                        is_pass.append(True)
                        print(dir)
                        utils.move_to(dir, 'db', 'Error')
                        break
                    elif decree == 't':
                        # Перенести папку в TRASH
                        is_pass.append(True)
                        print(dir)
                        utils.move_to(dir, 'db', 'Trash')
                        break
                    elif decree == 'l':
                        # Пропустить файл
                        is_pass.append(True)
                        break
                    elif decree == 'o':
                        # Открыть в EmEditor
                        subprocess.run(f'Emeditor {file.absolute()}')
                        utils.show_file(file)
                        console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')
                    elif decree == 'n':
                        # Открыть в Notepad++
                        subprocess.run(f'notepad++ {file.absolute()}')
                        utils.show_file(file)
                        console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')
                    elif decree == 'd':
                        # Изменить делиметр
                        delimiter = Prompt.ask('[magenta]Разделитель', choices=[':', ',', ';', r'\t'])
                        delimiter = '\t' if delimiter == '\\t' else delimiter
                        console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')
                    if not decree:
                        if not delimiter:
                            console.print("[yellow]Не указан разделитель")
                            # Изменить делиметр
                            delimiter = Prompt.ask('[magenta]Разделитель', choices=[':', ',', ';', r'\t'])
                            delimiter = '\t' if delimiter == '\\t' else delimiter
                            console.print(f'[magenta]Разделитель[/magenta]: "[red]{delimiter}[/red]"')
                        break
                if decree == 'l':
                    continue
                elif decree in ['p', 'e', 't']:
                    break

                skip = IntPrompt.ask('Пропустить строк', default=0)
                # delimiter = Prompt.ask('[magenta]Делитель', choices=[':', ',', ';', r'\t'])
                # delimiter = '\t' if delimiter == '\\t' else delimiter
                keys, colsname_plain = utils.get_keys(Prompt.ask('[cyan]Колонки'))

            rewrite_file = utils.csv_write_2(file, keys, colsname_plain, delimiter, skip)
            delimiter = ';' if delimiter == '\t' else delimiter

            # Проверка, не пустой ли файл
            assert rewrite_file.open('r', encoding='utf-8').read(1024)

            data_for_command = {
                'user': user,
                'password': password,
                'date': dir_as_db.date,
                'name': dir_as_db.name,
                'source': dir_as_db.source,
                'file': rewrite_file,
                'cols': colsname_plain,
                'delimiter': delimiter
            }

            #  Генерация и запись команды
            command.write(utils.get_db_command(**data_for_command))
            command.write(str(rewrite_file.absolute()) + "\n\n")

            is_pass.append(False)

        print(is_pass, all(is_pass))

        if len(is_pass) > 0 and not all(is_pass):
            utils.write_to_complete(dir, 'db')
        else:
            utils.write_to_passed_dirs(dir, 'db')
        command.close()
        print('\n')


def get_meta_for_db(dir: Path):
    path_to_readme = Path(os.path.join(str(dir.absolute()), 'readme.txt'))
    name = dir.absolute().parent.name
    source = ''
    date = ''

    if path_to_readme.exists():
        readme = path_to_readme.open(encoding=utils.get_encoding_file(path_to_readme))
        args = readme.readlines()
        i = 0
        date = args[i].replace("\n", "")
        source = utils.get_source_from_readme(path_to_readme)
    else:
        source = 'OLD DATABASE'

    # Если дата в неверном формате, то взять дату создания файла
    if not re.search(r'\d{4}-\d{2}-\d{2}', date):
        date = get_date_create(dir)
        print('Смена даты на', date)

    return name, date, source


def get_date_create(dir):
    path_to_dir_in_parsing_disk = str(dir.absolute())
    dates = []
    for item in utils.get_all_files_in_dir(dir):
        file_path = os.path.join(path_to_dir_in_parsing_disk, item)
        if os.path.isfile(file_path):
            file = Path(file_path)
            create_date = file.stat().st_mtime
            str_date = time.ctime(create_date)
            date = time.strptime(str_date)
            y, m, d = date.tm_year, date.tm_mon, date.tm_mday
            y = y if not y < 10 else f'0{y}'
            m = m if not m < 10 else f'0{m}'
            d = d if not d < 10 else f'0{d}'
            dates.append(f'{y}-{m}-{d}')
    date = min(dates)
    return date
