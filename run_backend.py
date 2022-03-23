import os
import requests
from backend.http_handler import HTTPHandler
from http.server import HTTPServer
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Backend for  the YADDB database!')
    parser.add_argument('-H', '--host', help='IP in the machine that will serve', default='0.0.0.0')
    parser.add_argument('-p', '--port', help='Port in which the app will run', default='19090')
    subparsers = parser.add_subparsers(dest='mode')
    subparsers.required = True
    mode_parser = subparsers.add_parser('slave')
    mode_parser.add_argument('--master-host', help='IP of the master node to sync', required=True)
    mode_parser.add_argument('--master-port', help='Port in which the app is running on master', required=True)
    mode_parser = subparsers.add_parser('master')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    print(args)
    if args.mode == 'slave':
        host, port, master_host, master_port = args.host, args.port, args.master_host, args.master_port
        res = requests.get(f'http://{master_host}:{master_port}/ping')
        if res.status_code == 200:
            print(f'Master {master_host} is alive and serving!')
            res = requests.post(f'http://{master_host}:{master_port}/subscribe', json={
                'ip': str(host),
                'port': str(port)
            })
            if not res.ok:
                print(f'Master {master_host} is not alive or is not serving!')
                exit(1)
            else:
                print(res.text)
        else:
            print(f'Master {master_host} is not alive or is not serving!')
            exit(1)
    else:
        os.environ['DB_NODE_MODE'] = args.mode
        host, port = args.host, args.port
    server = HTTPServer((host, int(port)), HTTPHandler)

    print('Running server!')

    server.serve_forever()