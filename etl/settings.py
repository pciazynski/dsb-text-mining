import os

try:
    from config import count, ctsns, datadir, webdir, copyrighttoken, tokenlength
except ModuleNotFoundError as error:
    if error.name != "config":
        raise
    from config_def import count, ctsns, datadir, webdir, copyrighttoken, tokenlength


def _resolve_path(value, env_name):
    path = os.environ.get(env_name, value)
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)
    return os.path.join(os.path.abspath(path), "")


datadir = _resolve_path(datadir, "DSB_DATADIR")
webdir = _resolve_path(webdir, "DSB_WEBDIR")
