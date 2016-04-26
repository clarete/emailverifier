# Copyright (c) 2015, Lincoln Clarete <lincoln@clarete.li>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#         1. Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the following
#   disclaimer.
#
#         2. Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided with
#   the distribution.
#
#         3. Neither the name of the copyright holder nor the names of
#   its contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import dns.resolver
import socket
import sys
import csv
import io


class ConnectionError(Exception): pass
class ParsingError(Exception): pass
class SMTPError(Exception): pass


def hash_parameters(args, kwargs):
    return hash(args) + hash(frozenset(kwargs.items()))


def memoize(func):
    memo = {}
    def helper(*args, **kwargs):
        key = hash_parameters(args, kwargs)
        if key not in memo:
            memo[key] = func(*args, **kwargs)
        return memo[key]
    helper.memo = memo
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
    return [x.strip() for x in io.open(path, 'rb').readlines()
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
        raise ConnectionError('Connection Error')
    output = sock.recv(1024).strip()
    if output[:3] != '220':
        raise SMTPError('HS: {0}'.format(output))
    sock.send('HELO FQDN\r\n')
    output = sock.recv(1024).strip()
    if output[:3] not in ('250', '220'):
        raise SMTPError('HELO: {0}'.format(output))
    sock.send('MAIL FROM:<mail@mail.com>\r\n')
    output = sock.recv(1024).strip()
    if output[:3] != '250':
        raise SMTPError('MAIL FROM: {0}'.format(output))
    sock.send('RCPT TO:<{0}>\r\n'.format(email))
    output = sock.recv(1024).strip()
    if output[:3] != '250':
        raise SMTPError('RCPT TO: {0}'.format(output))
    sock.close()
    return True

@debug
def checkemail(email):
    for host in getmxserversfromhost(gethostfromemail(email)):
        try:
            return connect(host.exchange.to_text(), email), ''
        except Exception:
            continue
    return None, "No email servers found"

def main(input_path, output_path):
    with io.open(output_path, 'wb') as output_file:
        output = csv.writer(output_file, dialect=csv.excel)
        output.writerow(['email', 'valid', 'error'])

        for email in getemailsfromfile(input_path):
            valid, error = checkemail(email)
            output.writerow([email, bool(valid), error])
            output_file.flush()

if __name__ == '__main__':
    main(input_path=sys.argv[1], output_path=sys.argv[2])
