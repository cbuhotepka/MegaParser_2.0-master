class AbstractDataBaseDir:

    def __init__(self, path, name, date, source):
        self.path = path
        self.name = name
        self.date = date
        self.source = source


class DataBaseDir(AbstractDataBaseDir):
    pass


class ComboDir(AbstractDataBaseDir):
    pass


class ComboFile:

    def __init__(self, colsname, delimiter):
        self.colsname = colsname
        self.delimiter = delimiter
