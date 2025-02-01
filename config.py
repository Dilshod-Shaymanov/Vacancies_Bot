from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
CHANNEL_ID = env.int("CHANNEL_ID")
ADMINS = env.list('ADMINS')