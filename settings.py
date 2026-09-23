from environs import Env

env = Env()
env.read_env()

TG_BOT_TOKEN = env.str("TG_BOT_TOKEN")
VK_BOT_TOKEN = env.str("VK_BOT_TOKEN")
REDIS_URL = env.str("REDIS_URL", default="redis://localhost:6379/0")
