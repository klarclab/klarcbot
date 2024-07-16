import discord
import json
import os
import asyncio
from collections import defaultdict
from time import time
from random import shuffle

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)
config = load_config()
TOKEN = config['token']
keyword = config['keyword']
default_replies = config['default_replies']
targets = config['targets']
mention_format = config.get('mention_format', '{reply} ||<@{user_id}>||')
reply_pools = {target: targets[target][:] for target in targets}
default_reply_pool = default_replies[:]
TOKEN_BUCKET_CAPACITY = 10
TOKENS_PER_INTERVAL = 1
TOKEN_REFILL_INTERVAL = 1
token_buckets = defaultdict(lambda: TOKEN_BUCKET_CAPACITY)
last_check = defaultdict(time)
last_sent_message = defaultdict(lambda: None)
client = discord.Client(self_bot=True)
config_last_modified_time = os.path.getmtime('config.json')
for pool in reply_pools.values():
    shuffle(pool)
shuffle(default_reply_pool)

# ---------------------------------------------------- #
@client.event
async def on_ready():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f'\033[91mLogged in as {client.user} (ID: {client.user.id})\033[0m')
    client.loop.create_task(check_for_config_updates())
def refill_tokens(author_id):
    now = time()
    elapsed = now - last_check[author_id]
    tokens_to_add = int(elapsed // TOKEN_REFILL_INTERVAL) * TOKENS_PER_INTERVAL
    if tokens_to_add > 0:
        token_buckets[author_id] = min(TOKEN_BUCKET_CAPACITY, token_buckets[author_id] + tokens_to_add)
    last_check[author_id] = now
def get_random_reply(pool):
    if not pool:
        pool.extend(config['default_replies'] if pool is default_reply_pool else targets[next(key for key, value in reply_pools.items() if value is pool)])
        shuffle(pool)
    return pool.pop()

# ---------------------------------------------------- #
@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return
    author_id = str(message.author.id)
    refill_tokens(author_id)
    if token_buckets[author_id] > 0:
        token_buckets[author_id] -= 1
    else:
        return
    if author_id in targets:
        reply = get_random_reply(reply_pools[author_id])
    else:
        if keyword.lower() in message.content.lower():
            reply = get_random_reply(default_reply_pool)
        else:
            return
    formatted_reply = mention_format.format(reply=reply, user_id=author_id)
    await message.channel.send(formatted_reply)
    last_sent_message[author_id] = reply

# ---------------------------------------------------- #
async def check_for_config_updates():
    global config, keyword, default_replies, targets, mention_format, reply_pools, default_reply_pool, config_last_modified_time
    while True:
        await asyncio.sleep(10)
        new_modified_time = os.path.getmtime('config.json')
        if new_modified_time != config_last_modified_time:
            config_last_modified_time = new_modified_time
            config = load_config()
            keyword = config['keyword']
            default_replies = config['default_replies']
            targets = config['targets']
            mention_format = config.get('mention_format', '{reply} ||<@{user_id}>||')
            reply_pools = {target: targets[target][:] for target in targets}
            default_reply_pool = default_replies[:]
            for pool in reply_pools.values():
                shuffle(pool)
            shuffle(default_reply_pool)
            print('reloaded config.json (changes detected)')

# ---------------------------------------------------- #
client.run(TOKEN)
