import asyncio
import os
import urllib.parse

import parse_header
from responses import AutoIndexResponse, FileResponse, NonExistResponse, InvalidMethodResponse, RedirectResponse

ROOT_PATH = '.'
LISTEN_ADDR = '127.0.0.1'
LISTEN_PORT = 8080


async def dispatch(reader, writer):
    headers_data = []
    while True:
        data = await reader.readline()
        headers_data.append(data.decode())
        # print(data)
        if data == b'\r\n' or data == b'':
            break

    client_headers = parse_header.HTTPHeader()
    for line in headers_data:
        client_headers.parse_header(line)

    method = client_headers.get('method')
    if method != 'GET' and method != 'HEAD':
        response = InvalidMethodResponse(method)
        writer.write(response.get_response())

    else:
        path = urllib.parse.unquote(client_headers.get('path'))
        part_range = client_headers.get('range')
        cookie = client_headers.get('cookie')

        if path == '/' and cookie and cookie.get('last') and cookie.get('last') != '/':
            response = RedirectResponse(method, cookie.get('last'))
            writer.write(response.get_response())

        else:
            real_path = ROOT_PATH + path

            try:
                if not os.path.isfile(real_path):
                    if path[-1:] != '/':
                        response = RedirectResponse(method, path + '/')
                        writer.write(response.get_response())
                    else:
                        response = AutoIndexResponse(method, path, real_path)
                        response.add_entry('..')
                        for filename in os.listdir(real_path):
                            if filename[0:1] != '.':
                                response.add_entry(filename)
                        writer.write(response.get_response())

                else:
                    response = FileResponse(method, real_path, part_range)
                    writer.write(response.get_response())

            except FileNotFoundError:
                response = NonExistResponse(method)
                writer.write(response.get_response())

    try:
        await writer.drain()
    except BrokenPipeError:
        pass
    writer.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(dispatch, LISTEN_ADDR, LISTEN_PORT, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
