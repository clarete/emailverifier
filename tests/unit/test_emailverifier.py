import main
import mock
import dns
import socket


def test_hash_parameters():
    "hash_parameters() should hash a tuple and a dictionary and returns its sum"

    # Given the following pair of args & kwargs
    args = ('a', 1)
    kwargs = {'b': 2}

    # When I hash them as many times as I want
    key = main.hash_parameters(args, kwargs)
    key2 = main.hash_parameters(args, kwargs)
    key3 = main.hash_parameters(args, kwargs)

    # Then I see it always generates the same int key
    key.should.be.an(int)
    key.should.equal(key2)
    key2.should.equal(key3)


def test_memoize():
    "@memoize() should cache the results of a function"

    # Given the following memoized function
    callback = mock.Mock(side_effect=lambda a, b: a+b)
    sum_function = main.memoize(callback)

    # When I call the function twice with the same parameters
    result = sum_function(1, 2)
    result2 = sum_function(1, 2)

    # Then I see the result is right
    result.should.equal(3)
    result2.should.equal(3)

    # And then I see the actual function was called just once
    callback.assert_called_once_with(1, 2)


def test_memoize():
    "@memoize() should NOT cache the results of a function called with different params"

    # Given the following memoized function
    callback = mock.Mock(side_effect=lambda a, b: a+b)
    sum_function = main.memoize(callback)

    # When I call the function twice with different parameters
    result = sum_function(1, 2)
    result2 = sum_function(2, 2)

    # Then I see the result is right
    result.should.equal(3)
    result2.should.equal(4)

    # And then I see the actual function was called just once
    callback.call_args_list.should.equal([mock.call(1, 2), mock.call(2, 2)])


@mock.patch('main.sys')
def test_debug(sys):
    "@debug() should print the func name before executing it, then print its output to stdout"

    # Given the following function, decorated with @debug
    function = mock.Mock(side_effect=lambda a, b: a+b, __name__='sum')
    decorated = main.debug(function)

    # When I call function()
    result = decorated(2, 2)

    # I see the results are right & that the debug info was properly
    # printed out
    result.should.equal(4)
    sys.stdout.write.call_args_list.should.equal([
        mock.call('sum: '),
        mock.call('4\n')
    ])


@mock.patch('main.io')
def test_getemailsfromfile(io):
    "getemailsfromfile(path) should return a list of emails read from a file (one per line)"

    # Given that the IO operation will return two email addresses
    io.open.return_value.readlines.return_value = \
        ['email1@host.com\n', 'email2@host.com\n']

    # When I try to get the list of emails
    emails = main.getemailsfromfile('/path/to/the/file.csv')

    # Then I see it read the emails returned from the file
    emails.should.equal(['email1@host.com', 'email2@host.com'])


def test_gethostfromemail():
    "gethostfromemail() should return the host part of an email address"

    # Given the following email address
    email = 'lincoln@clarete.li'

    # When I try to get its host name
    host = main.gethostfromemail(email)

    # Then I see it matches with the expected value
    host.should.equal('clarete.li')


def test_gethostfromemail_noatsign():
    "gethostfromemail() should return None if the address doesn't have the @ sign"

    # Given the following broken email address
    email = 'broken'

    # When I try to get its host name
    host = main.gethostfromemail(email)

    # Then the host should be None
    host.should.be.none


def test_getmxserversfromhost_when_host_is_none():
    "getmxserversfromhost() should return an empty list when host is None"

    main.getmxserversfromhost(None).should.equal([])
    main.getmxserversfromhost('').should.equal([])


@mock.patch('main.dns.resolver.query')
def test_getmxserversfromhost_noanswer(query):
    "getmxserversfromhost() should return an empty list on DNS lookup errors: NoAnswer"

    query.side_effect = dns.resolver.NoAnswer
    main.getmxserversfromhost('host.1').should.equal([])


@mock.patch('main.dns.resolver.query')
def test_getmxserversfromhost_emptylabel(query):
    "getmxserversfromhost() should return an empty list on DNS lookup errors: EmptyLabel"

    query.side_effect = dns.name.EmptyLabel
    main.getmxserversfromhost('host.2').should.equal([])


@mock.patch('main.dns.resolver.query')
def test_getmxserversfromhost_nxdomaian(query):
    "getmxserversfromhost() should return an empty list on DNS lookup errors: NXDOMAIAN"

    query.side_effect = dns.resolver.NXDOMAIN
    main.getmxserversfromhost('host.3').should.equal([])


@mock.patch('main.dns.resolver.query')
def test_getmxserversfromhost_nonameservers(query):
    "getmxserversfromhost() should return an empty list on DNS lookup errors: NoNameservers"

    query.side_effect = dns.resolver.NoNameservers
    main.getmxserversfromhost('host.4').should.equal([])


@mock.patch('main.dns.resolver.query')
def test_getmxserversfromhost_exception(query):
    "getmxserversfromhost() should return an empty list on DNS lookup errors: Exception (catch-all)"

    query.side_effect = Exception
    main.getmxserversfromhost('host.5').should.equal([])


def test_sockconnect():
    "sockconnect(sock, host) should connect the right port in the specified host"

    # Given the following socket object
    sock = mock.Mock()

    # When I try to connect to the specified host
    output = main.sockconnect(sock, 'clarete.li')

    # Then I see the connect method was called and the right port was
    # used
    output.should.equal(sock)
    output.connect.assert_called_once_with(('clarete.li', 25))


def test_sockconnect_attempt_different_ports():
    "socketconnect(sock, host) should attempt the following ports: 25, 465, 587 (order matters)"

    # Given the following socket object with a `.connect()` method
    # that always raises an error
    sock = mock.Mock(connect=mock.Mock(side_effect=socket.error))

    # When I try to connect to the specified host
    output = main.sockconnect(sock, 'clarete.li')

    # Then I see the connect method was called and the right port was
    # used
    output.should.equal(None)
    sock.connect.call_args_list.should.equal([
        mock.call(('clarete.li', 25)),
        mock.call(('clarete.li', 465)),
        mock.call(('clarete.li', 587)),
    ])


def test_connect_connectionerror():
    "connect(host, email) should raise ConnectionError if sockconnect() returns None"

    with mock.patch('main.socket.socket') as socket_class:

        # Given that our socket function will always return an error
        socket_class.return_value.connect.side_effect = socket.error

        # When we try to connect(), Then we see it raises the
        # exception we expect
        main.connect.when.called_with(
            'mx.clarete.li', 'lincoln@clarete.li'
        ).should.throw(
            main.ConnectionError, 'Connection Error')

def test_connect_no220_after_connect():
    "connect(host, email) should raise SMTPError if connection doesn't return 220"

    with mock.patch('main.socket.socket') as socket_class:

        # Given that our socket function will always return an error
        socket_class.return_value.recv.return_value = '550 Fuuuu'

        # When we try to connect(), Then we see it raises the
        # exception we expect
        main.connect.when.called_with(
            'mx.clarete.li', 'lincoln@clarete.li'
        ).should.throw(
            main.SMTPError, 'HS: 550 Fuuuu')


def test_connect_helo():
    "connect(host, email) should raise SMTPError if HELO response is not 220"

    with mock.patch('main.socket.socket') as socket_class:

        # Given that our socket function will always return an error
        socket_class.return_value.recv.side_effect = [
            '220 Successfuly Connected', # Response for connect
            '550 Fuuuu',                 # Response for HELO
        ]

        # When we try to connect(), Then we see it raises the
        # exception we expect
        main.connect.when.called_with(
            'mx.clarete.li', 'lincoln@clarete.li'
        ).should.throw(
            main.SMTPError, 'HELO: 550 Fuuuu')


def test_connect_mail_from():
    "connect(host, email) should raise SMTPError if MAIL FROM response is not 250"

    with mock.patch('main.socket.socket') as socket_class:

        # Given that our socket function will always return an error
        socket_class.return_value.recv.side_effect = [
            '220 Successfuly Connected', # Response for connect
            '220 Hi there',              # Response for HELO
            '550 NOOOOOOOO!'             # Response for MAIL FROM
        ]

        # When we try to connect(), Then we see it raises the
        # exception we expect
        main.connect.when.called_with(
            'mx.clarete.li', 'lincoln@clarete.li'
        ).should.throw(
            main.SMTPError, 'MAIL FROM: 550 NOOOOOOOO!')


def test_connect_rcpt_to():
    "connect(host, email) should raise SMTPError if RCPT TO response is not 250"

    with mock.patch('main.socket.socket') as socket_class:

        # Given that our socket function will always return an error
        socket_class.return_value.recv.side_effect = [
            '220 Successfuly Connected', # Response for connect
            '250 Hi there',              # Response for HELO
            '250 Sup!',                  # Response for MAIL FROM
            '??? User does not exist!'   # Response for RCPT TO
        ]

        # When we try to connect(), Then we see it raises the
        # exception we expect
        main.connect.when.called_with(
            'mx.clarete.li', 'lincoln@clarete.li'
        ).should.throw(
            main.SMTPError, 'RCPT TO: ??? User does not exist!')


def test_connect():
    "connect(host, email) should close the socket and return True if RCPT TO works"

    with mock.patch('main.socket.socket') as socket_class:

        # Given that our socket function will always return an error
        socket_class.return_value.recv.side_effect = [
            '220 Successfuly Connected', # Response for connect
            '250 Hi there',              # Response for HELO
            '250 Sup!',                  # Response for MAIL FROM
            '250 I know this addr!'      # Response for RCPT TO
        ]

        # When we try to connect()
        output = main.connect('mx.clarete.li', 'lincoln@clarete.li')

        # We see that the socket object was closed and that the output
        # was true
        socket_class.return_value.close.assert_called_once_with()
        output.should.be.true


def test_checkemail_nohosts():
    "checkemail(email) should return None if no hosts can be found for that email"

    main.checkemail('').should.equal((None, "No email servers found"))


@mock.patch('main.getmxserversfromhost')
def test_checkemail_cannot_connect_to_host(getmxserversfromhost):
    "checkemail(email) should return None if no email servers can be reached"

    # Given that our host returns two valid email servers
    server1 = mock.Mock()
    server2 = mock.Mock()
    getmxserversfromhost.return_value = [server1, server2]

    with mock.patch('main.connect') as connect:

        # And that connect will raise an exception for *both* servers
        # declared above
        connect.side_effect = [main.ConnectionError, Exception]

        # When I call checkemail()
        output = main.checkemail('lincoln@clarete.li')

        # Then I see we didn't get a valid answer
        output.should.equal((None, "No email servers found"))

        # And we also see that connect was attempted against both
        # email servers
        connect.call_args_list.should.equal([
            mock.call(server1.exchange.to_text(), 'lincoln@clarete.li'),
            mock.call(server2.exchange.to_text(), 'lincoln@clarete.li'),
        ])


@mock.patch('main.checkemail')
@mock.patch('main.getemailsfromfile')
@mock.patch('main.csv')
@mock.patch('main.io', mock.MagicMock())
def test_main(csv, getemailsfromfile, checkemail):
    "main(input_path, output_path) should read emails from `input_path` test them and write the result to `output_path`"

    # Given that I have a file that returns two email addresses
    getemailsfromfile.return_value = ['test@host.com', 'l@yo.com']

    # And, when we perform the check, one works and the other doesn't
    checkemail.side_effect = [(True, ''), (None, 'No email servers found')]

    # When we run the main function
    main.main('/input/file.csv', '/output/file.csv')

    # Then we see the right values predicted above were properly
    # written to the CSV file
    csv.writer.return_value.writerow.call_args_list.should.equal([
        mock.call(['email', 'valid', 'error']),
        mock.call(['test@host.com', True, '']),
        mock.call(['l@yo.com', False, 'No email servers found']),
    ])
