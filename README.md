# MegaParser_2.0
Пробегается по папкам, создавая новый файл в нужном формате и с выбранными колонками + генерирует команду для fix.py
## Подгтовка
1. Создайте в корне проекта CONFIG.env
с такими переменными:
```
PARSING_DISK_NAME=Z
USER_NAME=dr
USER_PASSWORD=drdrdr
```
2. Скопируйте с диска папку Source в C:\\ (В дальнейшем это можно будет изменять)
## Использование

1. ```python main.py```
2. Выберите тип папки db/combo
3. Выбор колонок в формате name_column=index(начинается с 1!) 
  Пример ```1=username, 2=userpass_plain, 3=user_additional_info, 5=address, 6=user_additional_info```
