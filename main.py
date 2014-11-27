import dns.resolver
import socket
import sys
import csv


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
    except:
        # Catch-all
        return []

@debug
def sockconnect(sock, host):
    ports = [25, 465, 587]
    for port in ports:
        try:
            sock.connect((host, port))
            return sock
        except socket.error:
            pass

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
    sock.send('RCPT TO: <{0}>\r\n'.format(email))
    if not sock.recv(1024)[:3] == '250':
        return None
    sock.close()
    return True

@debug
def checkemailhost(host, email):
    try:
        return connect(host, email).rcpt(email)
    except AttributeError:
        return None

@debug
def checkemail(email):
    for host in getmxserversfromhost(gethostfromemail(email)):
        return checkemailhost(host.exchange.to_text(), email)

def main(input_path, output_path):
    with open(output_path, 'wb') as output_file:
        output = csv.writer(output_file, dialect=csv.excel)
        output.writerow(['email', 'valid'])

        for email in getemailsfromfile(input_path):
            valid = checkemail(email)
            output.writerow([email, bool(valid)])
            output_file.flush()

if __name__ == '__main__':
    main(input_path=sys.argv[1], output_path=sys.argv[2])
