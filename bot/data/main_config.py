import argparse
import os

from bot.schemas.config import Config


parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["dev", "prod"], default=None)
parser.add_argument("other_args", nargs=argparse.REMAINDER)
args = parser.parse_args()
mode = args.mode
if not mode:
    mode = os.environ.get("MODE", "dev")
print(mode)

config = Config.get(mode)
IS_DEV = mode == 'dev'
