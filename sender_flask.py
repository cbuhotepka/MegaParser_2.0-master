import os
import shutil
import main
from rich.prompt import Prompt, Confirm
import requests
from loguru import logger
from tabulate import tabulate
from pathlib import Path
from rich.console import Console

console = Console()

Path(f"C:/Source/combo/fail_send.txt").touch()
Path(f"C:/Source/db/fail_send.txt").touch()

Path(f"C:/Source/combo/send_done.txt").touch()
Path(f"C:/Source/db/send_done.txt").touch()

PD = os.environ['PARSING_DISK_NAME']

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


HOST, PORT = '192.168.88.173', 9097


def get_cmds(f_list):
    f_list = list(filter(lambda x: x != '\n', f_list))
    f_list = list(map(lambda x: x.replace('\n', ''), f_list))
    return list(zip(f_list[::2], f_list[1::2]))


@logger.catch()
def client(cmd, path):
    url = f'http://{HOST}:{PORT}/'
    data = {'cmd': cmd}
    files = {'file': open(path, 'rb')}
    r = requests.post(url, data=data, files=files)
    return r.text


# client_path = input('Путь до клиента')
start_path = 'C:/Source/'

list_files = []
combo = Confirm.ask('Комбо?')
dir = start_path + 'combo' if combo else start_path + 'db'
done_parse = open(f'{dir}\\parsing_complete.txt', 'r', encoding='utf-8').readlines()
done_parse = list(filter(lambda x: x != '\n', done_parse))

fail_send = open(f'{dir}\\fail_send.txt', 'r', encoding='utf-8').readlines()
fail_send = list(filter(lambda x: x != '\n', fail_send))
fail_send = list(map(lambda x: x.replace('\n', ''), fail_send))

done_send_file = open(f'{dir}\\send_done.txt', 'r', encoding='utf-8')
done_send = list(filter(lambda x: x != '\n', done_send_file.readlines()))
done_send = list(map(lambda x: x.replace('\n', '').replace(f'{PD}:', 'C:'), done_send))
done_send_file.close()

# show_progress(complete, left)
print(Colors.WARNING + f'В ошибках - {len(fail_send)}')


def show_progress(done, left):
    a = int(round(done / (left + done), 2) * 100)
    bar = Colors.OKGREEN + '#' * a + Colors.ENDC + '-' * (100 - a)
    stat = f"Выполнено - {done}\n" \
           f"Осталось - {left}"
    print(f"<{bar}>" + f' {a}%')
    print(Colors.HEADER + stat)


# complete = len(os.listdir(dir.replace('C:/Source', f'{PD}:/Imported')))
# left = len(os.listdir(dir.replace('C:', f'{PD}:')))
# show_progress(complete, left)
print(Colors.WARNING + f'В ошибках - {len(fail_send)}')


@logger.catch()
def start():
    for line in done_parse:
        line = line.replace('\n', '')
        if line in done_send or line in fail_send:
            # пропуск если в готово или фейле)
            continue

        command_file = open(line + '\\_command_.txt', 'r', encoding='utf-8')
        cmds = get_cmds(command_file.readlines())
        answer = ''
        for cmd, path in cmds:
            cmd = cmd.replace('\ufeff', '')
            clr = ''
            if 'hash' in cmd.split('--colsname')[-1]:
                if '--algorithm' not in cmd:
                    clr = Colors.FAIL
                else:
                    clr = Colors.WARNING
            print(tabulate([[clr + cmd], [path]]))
            # if clr == Colors.FAIL:
            #   continue
            is_send = Prompt.ask('Отправляем?', choices=['hash', 'command', 'pass'],
                                 default='') if clr == Colors.FAIL else ''
            if is_send:
                if is_send == 'command':
                    cmd = Prompt.ask('Введите команду: ')
                    is_send = None
                elif is_send == 'hash':
                    print(*open(path, encoding='utf-8').readlines()[:5])
                    cmd += ' --algorithm ' + f"'{Prompt.ask('Введите тип хеша: ')}'"
                    is_send = None
                else:
                    continue
            # subprocess.run(f'python {client_path} --cmd "{cmd}" --path "{path}"')
            # print(cmd)
            with console.status('[bold green]Отправка...', spinner='point', spinner_style="bold blue"):
                answer = client(cmd, path)

            print(answer)
            if 'FATAL ERROR. This file cannot be repaired.' in answer:
                print(Colors.FAIL + "WARNING")
                print(Colors.WARNING + "--quotes append OK")
                cmd += ' --quotes '
                # is_resend = input(Colors.WARNING + 'Отправляем с --quotes? ')
                is_resend = False
                if not is_resend:
                    answer = client(cmd, path)
                    print(answer)
        print(line)
        user_input = Prompt.ask('Все ок?', choices=['fail'], default='')
        if not user_input:
            command_file.close()
            line_source = line.replace('C:\\Source', f'{PD}:\\Source')
            line_imported = line_source.replace(f'{PD}:\\Source', f'{PD}:\\Imported')
            if combo:
                path_source = Path(os.path.join(*Path(line_source).parts[:4]))
                path_imported = Path(os.path.join(*Path(line_imported).parts[:4]))
                shutil.move(str(path_source), str(path_imported))
            else:
                path_source = Path(os.path.join(*Path(line_source).parts[:5]))
                path_imported = Path(os.path.join(*Path(line_imported).parts[:5]))
                if not Path(os.path.join(*path_imported.parts[:4])).exists():
                    Path(os.path.join(*path_imported.parts[:4])).mkdir()
                shutil.move(str(path_source), str(path_imported))

            with open(f'{dir}\\send_done.txt', 'a', encoding='utf-8') as f:
                f.write(line_source + "\n")
            print('\033[32m ' + 'Перенос завершен')
        elif user_input == 'fail':
            with open(f"{dir}/fail_send.txt", 'a', encoding='utf-8') as f:
                f.write(line + '\n')


if __name__ == '__main__':
    start()
