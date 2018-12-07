import asyncio

LISTEN_ADDR = '127.0.0.1'
LISTEN_PORT = 5555


async def dispatch(reader, writer):
    while True:
        data = await reader.read(2048)
        if data and data != b'exit\r\n':
            writer.write(data)
            print('{} sent: {}'.format(writer.get_extra_info('peername'), data))
        else:
            break
    await writer.drain()
    writer.close()
        

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(dispatch, LISTEN_ADDR, LISTEN_PORT, loop=loop)
    server = loop.run_until_complete(coro)

    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
