import csv
import os
import subprocess
from pathlib import Path
from typing import Generator
from rich.prompt import Prompt, IntPrompt
from rich.console import Console

import utils
from MegaParser import ComboDir, AbstractDataBaseDir

user = os.environ.get('USER_NAME')
password = os.environ.get('USER_PASSWORD')
console = Console()


def start(auto_parse):
    start_path = os.path.join('C:\\', 'Source', 'combo')
    for p in ['parsing_complete.txt', 'passed_dirs.txt']:
        Path(os.path.join(start_path, p)).touch()
    iter_dirs = iter_for_combo(start_path)
    parse(iter_dirs, auto_parse)


def iter_for_combo(start_path):
    parsing_complete, passed_dirs = utils.get_list_dirs_for_pass(start_path)

    # Генератор, возвращает папку в каталоге ~/Source/combo
    for p in os.listdir(start_path):
        item = Path(os.path.join(start_path, p))
        if str(item.absolute()) in parsing_complete:
            console.print(f'[bold green]{item.absolute()}')
            continue
        elif str(item.absolute()) in passed_dirs:
            console.print(f'[bold yellow]{item.absolute()}')
            continue

        if item.is_dir():
            yield item


def parse(all_dirs: Generator, auto_parse):
    # Итерируемся по каталогам из генератора
    for dir in all_dirs:

        # (1) - Инициализация папки
        path_to_dir = str(dir.absolute())

        all_files = utils.get_all_files_in_dir(path_to_dir)
        if not all_files:
            console.print(f"[bold red]{path_to_dir} - Папка пуста")
            utils.write_to_passed_dirs(dir, 'combo')
            continue
        console.print(f"[bold cyan]{path_to_dir}")

        name, date, source = get_meta_for_combo(dir)
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
                    decree = Prompt.ask(f"[green]Если все ОК нажмите Enter", choices=['p', 'l', 'o', 'n', 'd', 'e', 't'], default='')
                    if decree == 'p':
                        # Пропустить все оставшееся
                        is_pass.append(True)
                        break
                    elif decree == 'e':
                        # Перенести папку в ERROR
                        is_pass.append(True)
                        print(dir)
                        utils.move_to(dir, 'combo', 'Error')
                        break
                    elif decree == 't':
                        # Перенести папку в TRASH
                        is_pass.append(True)
                        print(dir)
                        utils.move_to(dir, 'combo', 'Trash')
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
            command.write(utils.get_combo_command(**data_for_command))
            command.write(str(rewrite_file.absolute()) + "\n\n")

            is_pass.append(False)
            print(is_pass, all(is_pass))

        if len(is_pass) > 0 and not all(is_pass):
            utils.write_to_complete(dir, 'combo')
        else:
            utils.write_to_passed_dirs(dir, 'combo')
        command.close()
        print('\n')


def get_meta_for_combo(dir: Path):
    # Дата для комбо в названии папки в самом начале, отделена "_" от имени папки
    # Пример: 2020-01-11_17MB_840K_UserPass_HQ_COMBO__League_of_Legends_unchecked!

    data = dir.name.split('_', 2)
    date = data[0]
    name = data[2].replace('_', ' ')
    source = None

    path_to_readme = Path(os.path.join(str(dir.absolute()), 'readme.txt'))
    if path_to_readme.exists():
        source = utils.get_source_from_readme(path_to_readme)
    else:
        source = 'OLD COMBO'

    return name, date, source


