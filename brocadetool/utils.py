import yaml

def fetch_config(config_file):
    """Fetch configuration from file"""
    try:
        f = open(config_file)
    except IOError:
        raise

    config = yaml.load(f)
    f.close()

    return config
