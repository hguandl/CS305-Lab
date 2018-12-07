keys = ('method', 'path', 'range')


class HTTPHeader:
    def __init__(self):
        self.headers = {key: None for key in keys}

    def parse_header(self, line):
        fields = line.split(' ')
        if fields[0] == 'GET' or fields[0] == 'POST' or fields[0] == 'HEAD':
            self.headers['method'] = fields[0]
            self.headers['path'] = fields[1]
        if fields[0] == 'Range:':
            self.headers['range'] = fields[1]

    def get(self, key):
        return self.headers.get(key)
