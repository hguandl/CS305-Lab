#!/usr/bin/env python3

import curses
import socket
import time
import sys

import threading
import math

from raw_python import ICMPPacket, parse_icmp_header, parse_eth_header, parse_ip_header
from traceroute import single_ping_request, catch_ping_reply

# Init curses
stdscr = curses.initscr()
# Get height and width of the console
HEIGHT, WIDTH = stdscr.getmaxyx()
# Not to display cursor
curses.curs_set(0)


# Thread for update title time and catch quit
class MenuThread(threading.Thread):
    def __init__(self, header, menu):
        super().__init__()
        self.header = header
        self.menu = menu

    def run(self):
        while True:
            lock.acquire()
            # Update current time
            self.header.erase()
            self.header.addstr(get_header())
            self.header.refresh()
            self.menu.refresh()
            lock.release()
            # Wait for input
            c = self.menu.getch()
            # Received exit signal
            if c == ord('q'):
                global TO_EXIT
                TO_EXIT = True
                break
            time.sleep(1)


# A node for every step of traceroute
class TraceNode(object):
    def __init__(self, hostname):
        self.hostid = len(hosts)
        self.hostname = hostname
        self.cnt = 0        # Received ICMP echo
        self.snt = 0        # Total ICMP packets sent
        self.last = 0       # Last RTT
        self.avg = 0        # Average RTT
        self.best = -1      # Shorest RTT
        self.wrst = -1      # Longest RTT
        self.stdev = 0      # Standard deviation
        self.loss_rate = 0  # Loss rate

    # Keep the hostname unique in the list
    def __eq__(self, name: str):
        return self.hostname == name

    # Update statistics of RTT
    def update(self, rtt):
        self.snt += 1
        if rtt >= 0:
            if self.best == -1 or self.best > rtt:
                self.best = rtt
            if self.wrst == -1 or self.wrst < rtt:
                self.wrst = rtt
            self.avg = (self.avg * self.cnt + rtt) / (self.cnt + 1)
            self.stdev = math.sqrt((self.stdev * self.stdev * self.cnt + (self.avg - rtt) * (self.avg - rtt)) / (self.cnt + 1))
            self.cnt += 1
            self.last = rtt
        self.loss_rate = (1 - self.cnt / self.snt) * 100

    # Format the output to a row
    def output(self) -> str:
        return '{:4.1f}%{:6d} {:6.1f}{:6.1f}{:6.1f}{:6.1f}{:6.1f}\n'.format( \
                self.loss_rate, self.snt, self.last, self.avg, self.best, self.wrst, self.stdev)


# Thread for ping each node
class PingThread(threading.Thread):
    def __init__(self, tab):
        super().__init__()
        self.tab = tab

    def run(self):
        while True:
            if TO_EXIT:
                break
            for i in hosts:
                if TO_EXIT:
                    break
                # Bypass unknown host
                if i == '???':
                    continue
                # Execute ping
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 64)
                ping_id = single_ping_request(sock, i.hostname)
                lock.acquire()
                rtt, _, _, reached = catch_ping_reply(sock, ping_id, time.time())
                # Get a valid ping echo
                if reached and rtt is not None:
                    i.update(rtt * 1000)
                else:
                    i.update(-1)
                # Update & display RTT info
                rtt_tab.move(2 + i.hostid, 0)
                rtt_tab.addstr(i.output())
                rtt_tab.refresh()
                lock.release()
                time.sleep(0.1)


# Thread for traceroute
class TraceThread(threading.Thread):
    def __init__(self, host_list, rtt_tab):
        super().__init__()
        self.host_list = host_list
        self.rtt_tab = rtt_tab

    def run(self):
        while True:
            if TO_EXIT:
                break
            lock.acquire()
            # Execute ping
            addr, rtt, reached = ping(len(hosts) + 1, sys.argv[1])
            # Have reply
            if addr is not None:
                # A new host
                if not hosts.__contains__(addr):
                    tmp = TraceNode(addr)
                    hosts.append(tmp)
                    # Display the new host
                    self.host_list.addstr('{:2d}. {}\n'.format(len(hosts), addr))
                    tmp.update(rtt)
                    # Display the rtt info
                    self.rtt_tab.move(2 + tmp.hostid, 0)
                    self.rtt_tab.addstr(tmp.output())
            else:
                # Unknown host (no reply)
                hosts.append('???')
                self.host_list.addstr('{:2d}. {}\n'.format(len(hosts), '???'))
            self.host_list.refresh()
            self.rtt_tab.refresh()
            lock.release()
            if reached:
                break


# Exit signal for all threads
TO_EXIT = False

# Create raw socket
sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

# Names for each host
hosts = []

# Threads
threads = []
lock = threading.Lock()

# Localhost name + current time
def get_header() -> str:
    # localhost name
    host_str = '{} ({})'.format(socket.gethostname(), socket.gethostbyname(socket.gethostname()))
    # place current time from right
    time_str = time.asctime(time.localtime(time.time()))
    # use spaces to fill the middle of the line
    header_spaces = WIDTH - len(time_str) - len(host_str) - 1
    return host_str + ' ' * header_spaces + time_str

def ping(num, hostname) -> (str, float):
    # Set TTL
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, num)
    # Setup up an ICMP packet
    ID = single_ping_request(sock, hostname)
    # Execute ping
    rtt, reply, icmp_reply, reached = catch_ping_reply(sock, ID, time.time())
    # Fetched ICMP echo
    if reply:
        return reply['Source Address'], rtt * 1000, reached
    return None, None, False

def main(stdscr):
    # Set color
    curses.use_default_colors()

    # Title: MyTraceRoute, place to the middle
    title = curses.newwin(1, 0, 0, WIDTH // 2 - 6)

    # Header: localhost name + current time
    header = curses.newwin(1, 0, 1, 0)

    # Menu: [q]uit
    menu = curses.newwin(1, 0, 2, 0)
    # Not to wait for input
    menu.nodelay(True)

    # Every host during the routing
    host_list = curses.newwin(0, 0, 3, 0)

    # Table to display RTT statistics
    global rtt_tab
    rtt_tab = curses.newwin(0, 0, 3, WIDTH - 43)

    # Table header for rtt_tab
    rtt_tab_str = '  Packets               Pings\n' + \
                  'Loss%   Snt   Last   Avg  Best  Wrst StDev'

    # Contents of title
    title.addstr("MyTraceRoute", curses.A_BOLD)

    # Contents of menu
    menu.addstr('Keys:  ')
    menu.addch('q', curses.A_BOLD)
    menu.addstr('uit')

    # Title of host window
    host_list.addstr('\n Host\n', curses.A_BOLD)
    rtt_tab.addstr(rtt_tab_str, curses.A_BOLD)

    # Refresh windows
    menu.refresh()
    title.refresh()
    host_list.refresh()
    rtt_tab.refresh()
    header.clear()

    # Add threads to the list
    threads.append(MenuThread(header, menu))
    threads.append(TraceThread(host_list, rtt_tab))
    threads.append(PingThread(rtt_tab))

    # Run threads
    for t in threads:
        t.start()
    
    # Wait until all threads finish
    for t in threads:
        t.join()

    # Close the socket
    sock.close()

if __name__ == '__main__':
    # Need an arg as hostname
    if len(sys.argv) != 2:
        curses.endwin()
        print('Usage: python3 mtr.py hostname')
        sys.exit(2)

    # The window is too narrow
    if WIDTH < 52:
        curses.endwin()
        print('The width of console must at least than 52.')
        sys.exit(2)
    else:
        curses.wrapper(main)
