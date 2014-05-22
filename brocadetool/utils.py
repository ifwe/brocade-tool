import socket
import time
import yaml


def fetch_config(config_file):
    """
    Fetch configuration from file

    Args:
        config_file: Full path to configuration file that needs to be read

    Returns:
        Contents of config file in YAML format
    """
    try:
        f = open(config_file)
    except IOError:
        raise

    config = yaml.load(f)
    f.close()

    return config


def send_to_graphite(server, port, metric, value):
    """
    Send data to graphite

    Args:
        server: Graphite server
        port: Graphite port
        metric: Metric to send
        value: Metric value to send
    """
    now = time.time()
    msg = "%s %s %d\n" % (metric, value, now)

    sock = socket.socket()
    try:
        sock.connect((server, port))
        sock.sendall(msg)
    except:
        raise
    finally:
        sock.close()
