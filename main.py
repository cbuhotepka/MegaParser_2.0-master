from loguru import logger
from rich.prompt import Prompt
from rich.console import Console
from pathlib import Path
import argparse
from dotenv import load_dotenv

dotenv_path = Path('CONFIG.env')
assert dotenv_path.exists()
load_dotenv(dotenv_path)

from combo_parsing import start as start_combo_parse

from db_parsing import start as start_db_parse

console = Console()
parser = argparse.ArgumentParser(description="MegaParser 2.0")


@logger.catch()
def start_parsing(auto_parse):
    type_dir = Prompt.ask('Тип папки', choices=['combo', 'db'])
    if type_dir == 'combo':
        start_combo_parse(auto_parse)
    else:
        start_db_parse(auto_parse)


if __name__ == '__main__':
    parser.add_argument("--auto-parse", dest="auto_parse", action='store_true')

    args = parser.parse_args()
    try:
        start_parsing(auto_parse=args.auto_parse)
    except KeyboardInterrupt:
        console.print('[green]\nВЫХОД...')
