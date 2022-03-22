from math import ceil
import os
import requests
from frontend.router import makeHTTPHandler
from http.server import HTTPServer
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '-H', '--host', help='IP in the machine that will serve', default='0.0.0.0')
    parser.add_argument(
        '-p', '--port', help='Port in which the app will run', default='19090')
    parser.add_argument(
        '--nodes', nargs='+', help='IPs and ports of the machines that will run the distributed server. (0.0.0.0:19090)', required=True)
    return args


if __name__ == '__main__':
    args = parse_args()

    dht_lookup = {}

    with requests.Session() as r:
        for node in args.nodes:
            ip, port = node.split(':')
            for octet in ip.split('.'):
                if int(octet) < 0 or int(octet) > 255:
                    raise Exception(f'{ip} is not a valid ip!')
            if int(port) < 0 or int(port) > 2**16 - 1:
                raise Exception(f'{port} is not a valid port!')
            res = r.get(f'http://{node}/ping')
            if res.ok:
                print(f'Node {node} is alive!')
        
        size = 2 ** 128

        per_node = int(size / len(args.nodes))

        last_end = -1

        o = size % len(args.nodes)

        iterator = enumerate(args.nodes)

        while last_end < size:
            id, node = next(iterator)
            start = last_end + 1
            if o > 0:
                o -= 1
                end = start + per_node + 1
            else:
                end = start + per_node
            last_end = end

            start = start.to_bytes(128//8, byteorder='big').hex()
            end = end.to_bytes(128//8, byteorder='big').hex()

            res = r.post(f'http://{node}/join', json={
                "id": str(id),
                "start": start,
                "end": end
            })

            if res.ok:
                print(f'Node {node} joined the cluster with start={start} and end={end}')
            else:
                print(f'Node {node} did not join! message="{res.text}"')
                print('Aborting')
                exit(1)
            
            dht_lookup[(bytes.fromhex(start), bytes.fromhex(end))] = node
        
    

            
            

    server = HTTPServer((args.host, int(args.port)), makeHTTPHandler(args.nodes))

    print('Running server!')

    server.serve_forever()
