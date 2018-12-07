keys = ('method', 'path', 'range', 'cookie')


class HTTPHeader(object):
    def __init__(self):
        self.headers = {key: None for key in keys}

    def parse_header(self, line):
        fields = line.split(' ')
        if fields[0] == 'GET' or fields[0] == 'POST' or fields[0] == 'HEAD':
            self.headers['method'] = fields[0]
            self.headers['path'] = fields[1]
        if fields[0] == 'Range:':
            self.headers['range'] = HTTPRange(fields[1][:-2]).get_range()
        if fields[0] == 'Cookie:':
            self.headers['cookie'] = HTTPCookie(fields[1][:-2])

    def get(self, key):
        return self.headers.get(key)


class HTTPCookie(object):
    def __init__(self, string):
        self.__cookie = {}
        items = string.split(';')
        for i in items:
            entry = i.split('=')
            self.__cookie[entry[0]] = entry[1]

    def get(self, entry):
        if entry in self.__cookie:
            return self.__cookie[entry]
        else:
            return None


class HTTPRange(object):
    def __init__(self, string):
        self.__start = None
        self.__end = None
        parts = string.split('=')
        if parts[0] == 'bytes':
            range_int = parts[1].split('-')
            if range_int[0] != '':
                self.__start = int(range_int[0])
            else:
                self.__start = 0
            if range_int[1] != '':
                self.__end = int(range_int[1])
            else:
                self.__end = -1

    def get_range(self) -> (int, int):
        if self.__start is not None and self.__end is not None:
            return self.__start, self.__end
        else:
            return None
