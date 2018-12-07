import html
import os
import urllib.parse

from mime_types import mime_types

_version = '1.0.0'


class Response(object):
    def __init__(self, method, version, code, message):
        self.method = method
        self.version = version
        self.code = code
        self.message = message
        self.headers = {'Server': 'GH-AutoIndex/' + _version,
                        'Connection': 'close'}
        self.body = ''

    def get_headers(self) -> bytes:
        headers = str.format('HTTP/%s %s %s\r\n' % (self.version, self.code, self.message))
        for key in self.headers:
            headers += str.format('%s: %s\r\n' % (key, self.headers[key]))
        headers += '\r\n'
        return headers.encode()

    def get_body(self) -> bytes:
        return self.body.encode()

    def get_response(self) -> bytes:
        if self.method == 'HEAD':
            return self.get_headers()
        elif self.method == 'GET':
            return self.get_headers() + self.get_body()
        else:
            return b''


class ErrorResponse(Response):
    def __init__(self, method, code, message):
        super().__init__(method, '1.0', code, message)
        self.headers['Content-Type'] = 'text/html; charset=utf-8'
        self.body = str.format('<html><head><title>%s %s</title></head>\r\n'
                               '<body bgcolor="white">\r\n'
                               '<center><h1>%s %s</h1></center>\r\n'
                               '<hr><center>GH-AutoIndex/%s</center>\r\n'
                               '</body></html>\r\n' % 
                               (code, message, code, message, _version))


class AutoIndexResponse(Response):
    def __init__(self, method, path, real_path):
        super().__init__(method, '1.0', '200', 'OK')
        self.headers['Content-Type'] = 'text/html; charset=utf-8'
        self.path = path
        self.real_path = real_path
        title = html.escape(path)
        self.contentStart = ('<html><head><title>Index of ' + title + '</title></head>\r\n'
                             '<body bgcolor="white">\r\n'
                             '<h1>Index of ' + title + '</h1><hr>\r\n'
                             '<pre>\r\n')
        self.contentEnd = ('</pre>\r\n'
                           '<hr>\r\n'
                           '</body></html>\r\n')
        self.folders = []
        self.files = []
        self.last_dir = None

    def add_entry(self, name):
        if not os.path.isfile(self.real_path + name):
            name += '/'
            link = urllib.parse.quote(name)
            text = html.escape(name)
            self.folders.append(str.format('<a href="%s">%s</a>\r\n' % (link, text)))
            self.last_dir = urllib.parse.quote(self.path)
        else:
            link = urllib.parse.quote(name)
            text = html.escape(name)
            self.files.append(str.format('<a href="%s">%s</a>\r\n' % (link, text)))

    def get_body(self) -> bytes:
        content = self.contentStart
        for entry in self.folders:
            content += entry
        for entry in self.files:
            content += entry
        content += self.contentEnd
        return content.encode()

    def get_headers(self) -> bytes:
        self.headers['Set-Cookie'] = str.format('last=%s; Path=/' % self.last_dir)
        self.headers['Content-Length'] = str.format('%d' % len(self.get_body()))
        return super().get_headers()


class FileResponse(Response):
    def __init__(self, method, path, part_range):
        super().__init__(method, '1.1', '200', 'OK')
        self.path = path
        self.size = os.path.getsize(path)
        self.part_range = part_range

        self.headers['Content-Type'] = self.__file_type()
        self.headers['Accept-Ranges'] = 'bytes'

        if part_range is not None:
            self.code = '206'
            self.message = 'Partial Content'
            self.start, self.end = part_range[0], part_range[1]
            if self.end < 0:
                self.end = self.size + self.end
            self.headers['Content-Range'] = str.format('bytes %d-%d/%d' % 
                                                       (self.start, self.end, self.size))
            self.headers['Content-Length'] = str(self.end - self.start + 1)

        else:
            self.headers['Content-Length'] = str(self.size)

    def __file_type(self) -> str:
        f_type = mime_types.get(self.path.split('.')[-1])
        if not f_type:
            f_type = 'Application/octet-stream'
        return f_type

    def get_body(self) -> bytes:
        with open(self.path, 'rb') as file:
            if self.part_range is not None:
                file.seek(self.start, 0)
                return file.read(self.end - self.start + 1)
            else:
                return file.read()


class NonExistResponse(ErrorResponse):
    def __init__(self, method):
        super().__init__(method, '404', 'Not Found')


class InvalidMethodResponse(ErrorResponse):
    def __init__(self, method):
        super().__init__(method, '405', 'Method Not Allowed')


class RedirectResponse(ErrorResponse):
    def __init__(self, method, path):
        super().__init__(method, '302', 'Found')
        self.headers['Location'] = path
