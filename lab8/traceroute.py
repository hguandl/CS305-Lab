import struct
import random
import select
import socket
import time
import sys

from raw_python import ICMPPacket, parse_icmp_header, parse_eth_header, parse_ip_header

def calc_rtt(time_sent):
    return time.time() - time_sent

def single_ping_request(s, addr=None):
    # Random Packet Id
    pkt_id = random.randrange(10000, 65000)

    # Create ICMP Packet
    packet = ICMPPacket(_id=pkt_id).raw

    # Send ICMP Packet
    while packet:
        sent = s.sendto(packet, (addr, 1))
        packet = packet[sent:]

    return pkt_id

def catch_ping_reply(s, ID, time_sent, timeout=1):
    # create while loop
    while True:
        starting_time = time.time()  # Record Starting Time

        # to handle timeout function of socket
        process = select.select([s], [], [], timeout)

        # check if timeout
        if not process[0]:
            return calc_rtt(time_sent), None, None, False

        # receive packet
        rec_packet, addr = s.recvfrom(1024)

        # extract icmp packet from received packet 
        icmp = parse_icmp_header(rec_packet[20:28])

        # return every icmp response
        return calc_rtt(time_sent), parse_ip_header(rec_packet[:20]), icmp, icmp['id'] == ID

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

    # need hostname
    if len(sys.argv) != 2:
        sys.exit(2)

    print('traceroute to {} ({})'.format(sys.argv[1], socket.gethostbyname(sys.argv[1])))

    step = 0
    while True:
        step += 1
        hostname = None
        rtt_str= ''
        # Set TTL
        s.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, step)
        for i in range(3):
            # Send ping
            ID = single_ping_request(s, sys.argv[1])
            rtt, reply, icmp_reply, reached = catch_ping_reply(s, ID, time.time())

            # Record reply
            if reply:
                hostname = reply['Source Address']
                rtt_str += '  {:.2f} ms'.format(rtt * 1000)
            else:
                rtt_str += ' *'
        # The server sent reply
        if hostname is not None:
            print('{0:2d}  {1} ({1}){2}'.format(step, hostname, rtt_str))
        # The server ignored ping or lost
        else:
            print('{:2d}  * * *'.format(step))
        if reached:
            break

    # close socket
    s.close()

if __name__ == '__main__':
    main()