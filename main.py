import dns.resolver
import socket
import sys


def memoize(func):
    memo = {}
    def helper(x, *args, **kwargs):
        if x not in memo:
            memo[x] = func(x, *args, **kwargs)
        return memo[x]
    return helper

def debug(func):
    def wrapper(*args, **kwargs):
        sys.stdout.write('{0}: '.format(func.__name__))
        sys.stdout.flush()
        output = func(*args, **kwargs)
        sys.stdout.write('{0}\n'.format(output))
        return output
    return wrapper

def getemailsfromfile(path):
    return [x.strip() for x in open(path).readlines()
        if x.strip()]

@debug
def gethostfromemail(email):
    try:
        return email.split('@')[1]
    except IndexError:
        return None

@memoize
@debug
def getmxserversfromhost(host):
    if not host:
        return []
    try:
        return dns.resolver.query(host, 'MX')
    except dns.resolver.NoAnswer:
        return []
    except dns.name.EmptyLabel:
        return []
    except dns.resolver.NXDOMAIN:
        return []
    except dns.resolver.NoNameservers:
        # We might still want to try to return host
        return []

@debug
def sockconnect(sock, host):
    ports = [25, 465, 587]
    for port in ports:
        try:
            sock.connect((host, port))
            return sock
        except socket.error:
            continue

@debug
def connect(host, email):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if not sockconnect(sock, host):
        return None
    if not sock.recv(1024)[:3] == '220':
        return None
    sock.send('HELO\r\n')
    if not sock.recv(1024)[:3] == '250':
        return None
    sock.send('RCPT TO: <{0}>\r\n', email)
    if not sock.recv(1024)[:3] == '250':
        return None
    sock.close()
    return True

@debug
def checkemail(host, email):
    try:
        return connect(host, email).rcpt(email)
    except AttributeError:
        return None

def main(path):
    for email in getemailsfromfile(path):
        for host in getmxserversfromhost(gethostfromemail(email)):
            if checkemail(host.exchange.to_text(), email):
                break

if __name__ == '__main__':
    main(path=sys.argv[1])
