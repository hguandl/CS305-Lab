import html
import os
import urllib.parse

from mime_types import mime_types


class AutoIndexResponse(object):
    def __init__(self, path, real_path):
        self.headersStart = ('HTTP/1.0 200 OK\r\n'
                        'Content-Type:text/html; charset=utf-8\r\n'
                        'Server: GH-AutoIndex\r\n'
                        'Connection: close\r\n')
        self.headersEnd = '\r\n'
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

    def add_entry(self, name):
        if not os.path.isfile(self.real_path + name):
            name += '/'
            link = urllib.parse.quote(name)
            text = html.escape(name)
            self.folders.append(str.format('<a href="%s">%s</a>\r\n' % (link, text)))
        else:
            link = urllib.parse.quote(name)
            text = html.escape(name)
            self.files.append(str.format('<a href="%s">%s</a>\r\n' % (link, text)))

    def get_content(self) -> bytes:
        content = self.contentStart
        for entry in self.folders:
            content += entry
        for entry in self.files:
            content += entry
        content += self.contentEnd
        return content.encode()

    def get_headers(self) -> bytes:
        headers = self.headersStart
        headers += str.format('Content-Length: %d\r\n' % (len(self.get_content())))
        headers += self.headersEnd
        return headers.encode()

    def get_response(self) -> bytes:
        return self.get_headers() + self.get_content()


class FileResponse(object):
    def __init__(self, path, part_range):
        self.path = path
        self.size = os.path.getsize(path)
        self.start = None
        self.end = None

        if part_range is not None:
            self.start, self.end = part_range[0], part_range[1]
            if self.end < 0:
                self.end = self.size + self.end
            self.headers = ('HTTP/1.0 206 Partial Content\r\n'
                            'Server: GH-AutoIndex\r\n')
            self.headers += 'Content-Type: ' + self.__file_type() + '\r\n'
            self.headers += str.format('Content-Range: bytes %d-%d/%d\r\n' %
                                       (self.start, self.end, self.size))
            self.headers += 'Connection: close\r\n'
            self.headers += 'Content-Length: ' + str(self.end - self.start + 1) + '\r\n\r\n'

        else:
            self.headers = ('HTTP/1.0 200 OK\r\n'
                            'Server: GH-AutoIndex\r\n')
            self.headers += 'Content-Type: ' + self.__file_type() + '\r\n'
            self.headers += 'Connection: close\r\n'
            self.headers += 'Content-Length: ' + str(self.size) + '\r\n'
            self.headers += 'Accept-Ranges: bytes\r\n\r\n'

    def __file_type(self) -> str:
        f_type = mime_types.get(self.path.split('.')[-1])
        if not f_type:
            f_type = 'Application/octet-stream'
        return f_type

    def get_headers(self) -> bytes:
        return self.headers.encode()

    def get_content(self) -> bytes:
        file = open(self.path, 'rb')
        if self.start is not None:
            file.seek(self.start, 0)
            ret = file.read(self.end - self.start + 1)
        else:
            ret = file.read()
        file.close()
        return ret

    def get_response(self) -> bytes:
        return self.get_headers() + self.get_content()


class NonExistResponse(object):
    def __init__(self):
        self.headers = ('HTTP/1.0 404 Not Found\r\n'
                        'Content-Type:text/html; charset=utf-8\r\n'
                        'Server: GH-AutoIndex\r\n'
                        'Connection: close\r\n'
                        '\r\n')

        self.content = ('<html>\r\n'
                        '<head><title>404 Not Found</title></head>\r\n'
                        '<body bgcolor="white">\r\n'
                        '<center><h1>404 Not Found</h1></center>\r\n'
                        '<hr><center>GH-AutoIndex/0.1.2</center>\r\n'
                        '</body>\r\n'
                        '</html>\r\n')

    def get_headers(self) -> bytes:
        return self.headers.encode()

    def get_content(self) -> bytes:
        return self.content.encode()

    def get_response(self) -> bytes:
        return self.get_headers() + self.get_content()


class InvalidMethodResponse(object):
    def __init__(self):
        self.headers = ('HTTP/1.0 405 Method Not Allowed\r\n'
                        'Content-Type:text/html; charset=utf-8\r\n'
                        'Server: GH-AutoIndex\r\n'
                        'Connection: close\r\n'
                        '\r\n')

        self.content = ('<html>\r\n'
                        '<head><title>405 Method Not Allowed</title></head>\r\n'
                        '<body bgcolor="white">\r\n'
                        '<center><h1>405 Method Not Allowed</h1></center>\r\n'
                        '<hr><center>GH-AutoIndex/0.1.2</center>\r\n'
                        '</body>\r\n'
                        '</html>\r\n')

    def get_headers(self) -> bytes:
        return self.headers.encode()

    def get_content(self) -> bytes:
        return self.content.encode()

    def get_response(self) -> bytes:
        return self.get_headers() + self.get_content()