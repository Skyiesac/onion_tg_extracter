import re
import json
import asyncio
import os
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
channel_username = 'toronionlinks' 
output_file = 'onion_links.json'
last_id_file = 'last_message_id.txt'


onion_regex = r'(http[s]?://)?([a-z2-7]{16,56}\.onion)\b'


def load_last_message_id():
    if os.path.exists(last_id_file):
        with open(last_id_file, 'r') as f:
            return int(f.read().strip())
    return 0


def save_last_message_id(message_id):
    with open(last_id_file, 'w') as f:
        f.write(str(message_id))


def save_json_line(data):
    with open(output_file, 'a') as f:
        json.dump(data, f)
        f.write('\n')


async def main():
    client = TelegramClient('session', api_id, api_hash)
    await client.start()

    last_id = load_last_message_id()
    max_id = 0
    total_found = 0

    try:
        async for message in client.iter_messages(channel_username, min_id=last_id):
            if message.id > max_id:
                max_id = message.id

            if message.message:
                found = re.findall(onion_regex, message.message)
                for match in found:
                    full_url = f"http://{match[1]}"
                    json_obj = {
                        "source": "telegram",
                        "url": full_url,
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                        "context": f"Found in Telegram channel @{channel_username}",
                        "status": "pending"
                    }
                    save_json_line(json_obj)
                    total_found += 1

        if max_id > last_id:
            save_last_message_id(max_id)

        print(f"Extraction complete. {total_found} .onion links saved.")

    except FloodWaitError as e:
        print(f"Rate limited. Wait for {e.seconds} seconds.")
    except Exception as e:
        print(f" An Error occured: {e}")
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
