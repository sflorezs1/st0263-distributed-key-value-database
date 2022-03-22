from backend.http_handler import HTTPHandler
from http.server import HTTPServer


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9090), HTTPHandler)
    server.serve_forever()