import requests
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Set

class DiscordCrawler:

    def __init__(self, channel_list: List[str], bot_token: str, webhook_url: str, target_user_ids: List[str]):
        self.channel_list = channel_list
        self.request_count = 0

        self.bot_token = bot_token
        self.webhook_url = webhook_url
        self.api_urls = {}
        self.initial_messages = {}
        self.target_user_ids = set(target_user_ids)

        self.last_request_time = 0
        self.last_log_time = 0

        self.api_urls: Dict[int, str] = {
            channel_id: f"https://discord.com/api/v10/channels/{channel_id}/messages"
            for channel_id in self.channel_list
        }
        self.seen_message_ids: Dict[int, Set[str]] = {
            channel_id: set() for channel_id in self.channel_list
        }

    def update_channel_list(self, new_channel_list: List[str]):
        if self.channel_list == new_channel_list:
            return

        for channel_id in new_channel_list:
            if channel_id not in self.channel_list:
                with open("monitorbot.log", "a") as f:
                    f.write(f"# New channel Detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --- **{new_channel_list[channel_id]}** detected\n")
                self.api_urls[channel_id] = f"https://discord.com/api/v10/channels/{channel_id}/messages"
                self.seen_message_ids[channel_id] = set()
                retries = 3
                while retries != 0:
                    new_messages = self.fetch_messages(api_url=self.api_urls[channel_id])
                    if new_messages is None:
                        retries -= 1
                        continue
                    for message in new_messages:
                        message_id = message.get("id")
                        if message_id is not None:
                            self.seen_message_ids[channel_id].add(message_id)

        for channel_id in self.channel_list:
            if channel_id not in new_channel_list:
                with open("monitorbot.log", "a") as f:
                    f.write(f"# Original channel Deleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --- **{self.channel_list[channel_id]}** deleted\n")
                del self.api_urls[channel_id]
                del self.seen_message_ids[channel_id]

        self.channel_list = new_channel_list

        with open("monitorbot.log", "a") as f:
            f.write(f"# Channel updated successfully.\n")

    def _wait_for_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < 2.0:
            time.sleep(2.0)

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.bot_token,
            "Content-Type": "application/json"
        }
    
    def fetch_messages(self, limit: int = 10, api_url: str = "", before=None) -> List[Dict]:
        """Fetch recent messages from the channel"""
        headers = self.get_headers()
        params = {"limit": limit}
        if before:
            params["before"] = before

        retries = 5

        while retries > 0:
            print(f"Retrying # {6 - retries}: ", flush=True)
            try:
                self._wait_for_rate_limit()
                response = requests.get(api_url, headers=headers, params=params, timeout=15)
                self.last_request_time = time.time()
                self.request_count += 1
                print(datetime.now())
                print(f"{response.status_code}", flush=True)
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error fetching messages: {response.status_code} {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Error fetching messages: {e}")
                retries -= 1

        print("Failed to fetch messages")
        return []
    
    def is_target_user_message(self, message: Dict) -> bool:
        """Check if message is from a target user"""
        author_id = message.get("author", {}).get("id")
        return author_id in self.target_user_ids

    def is_twitter_hold(self, message: Dict) -> Dict:
        "Check if message holds twitter url"
        content = message.get("content", "")
        return "https://x.com/" in content or "https://twitter.com/" in content

    def is_announcement(self, message: Dict) -> bool:
        content = message.get("content", "")
        mention_roles = message.get("mention_roles", [])
        if mention_roles:
            return True

        lowered = content.lower()
        return (
            "this is an unclaimed subnet." in lowered
            or "announcement" in lowered
        )

    def create_embed(self, message: Dict, channel_id: int) -> Dict:
        """Create Discord embed from message data"""
        author = message.get("author", {})
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        # Format timestamp

        channel_name = self.channel_list.get(channel_id, str(channel_id))
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            formatted_time = timestamp

        if self.is_twitter_hold(message):
            title = f"New Twitter post in **{channel_name}**"
            color = 0xFFFF00
        elif self.is_announcement(message):
            title = f"New announcement in **{channel_name}**"
            color = 0x00FFFF
        elif self.is_target_user_message(message):
            title = f"Const said something in **{channel_name}**"
            color = 0xFFFFFF
        else:
            title = f"New message in **{channel_name}**"
            color = 0x808080

        # Create embed
        embed = {
            "title": title,
            "description": content[:4096] if content else "*No text content*",  # Discord embed limit
            "color": color,
            "timestamp": timestamp,
            "author": {
                "name": f"{author.get('global_name', author.get('username', 'Unknown'))}",
                "icon_url": f"https://cdn.discordapp.com/avatars/{author.get('id')}/{author.get('avatar')}.png" if author.get('avatar') else None
            },
            "fields": [
                {
                    "name": "Channel",
                    "value": f"<#{channel_id}>",
                    "inline": True
                }
            ]
        }
        avatar = author.get("avatar")
        author_id = author.get("id")
        if avatar in author_id:
            embed["author"]["icon_url"] = (
                f"https://cdn.discordapp.com/avatars/{author_id}/{avatar}.png"
            )

        return embed
    
    def send_webhook_message(self, embeds: List[Dict]):
        """Send message to webhook"""
        if not embeds:
            return

        for embed in embeds:
            payload = {
                "content": "@everyone",
                "embeds": [embed],
                "username": "BT Monitor",
                "avatar_url": embed["author"]["icon_url"]
            }
            
            retries = 5
            while retries > 0:
                try:
                    self._wait_for_rate_limit()
                    response = requests.post(self.webhook_url, json=payload, timeout=15)
                    self.request_count += 1
                    self.last_request_time = time.time()

                    if response.status_code in [200, 204]:
                        print(f"Successfully sent {len(embeds)} message(s) to webhook")
                        return
                    else:
                        print(f"Failed to send webhook: {response.status_code} {response.text}")
                        retries -= 1
                        time.sleep(2)
                except Exception as e:
                    print(f"Error sending webhook: {e}")
                    retries -= 1
                    time.sleep(2)
            print("Failed to send webhook")

    def process_new_messages(self, channel_id: int):
        """Process new messages and send to webhook"""
        api_url = self.api_urls[channel_id]
        seen_ids = self.seen_message_ids[channel_id]

        new_messages = []
        new_message_ids = set()
        common_msg = False
        before = None
        messages = []

        while not common_msg:
            batch = self.fetch_messages(api_url=api_url, before=before)
            if not batch:
                break

            messages.extend(batch)

            for message in batch:
                message_id = message.get("id")
                if not message_id:
                    continue
                if message_id in seen_ids:
                    common_msg = True
                    break

            if not common_msg:
                before = batch[-1].get("id")
                if not before:
                    break

        message_ids = []
        for message in messages:
            message_ids.append(message.get("id"))

        print("all message processed")

        for message in messages:
            message_id = message.get("id")
            if not message_id:
                continue

            new_message_ids.add(message_id)

            # Check if this is a new message from a target user
            if (
                message_id not in seen_ids
                and (
                    self.is_twitter_hold(message) 
                    or self.is_announcement(message) 
                    or self.is_target_user_message(message)
                )
            ):
                new_messages.append(message)
                print(f"Found new message from {message.get('author', {}).get('username', 'Unknown')}: {message.get('content', '')[:50]}...")

        # Update seen message IDs
        seen_ids.update(new_message_ids)
        self.seen_message_ids[channel_id] = seen_ids
        
        # Send new messages to webhook
        if new_messages:
            embeds = [self.create_embed(msg, channel_id) for msg in reversed(new_messages)]
            self.send_webhook_message(embeds)
        else:
            print(f"No new messages from {self.channel_list[channel_id]}")

    def run(self, check_interval: int = 60):
        """Run the crawler with specified interval in seconds"""
        print(f"Starting Discord crawler...")
        
        total_initial = 0
        for channel_id in self.channel_list:
            init_messages = self.fetch_messages(api_url=self.api_urls[channel_id])
            self.initial_messages[channel_id] = init_messages

            for message in init_messages:
                message_id = message.get("id")
                if message_id:
                    self.seen_message_ids[channel_id].add(message_id)

            total_initial += len(init_messages)

        print(f"Initial fetch complete. Found {total_initial} existing messages.")

        # Start monitoring loop
        while True:
            # Update Channel list from outside

            with open("channel_list_1.json", "r", encoding="utf-8") as f:
                CHANNEL_LIST = json.load(f)

            self.update_channel_list(CHANNEL_LIST)

            try:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new messages...")
                for channel_id in self.channel_list:
                    self.process_new_messages(channel_id)
                    time.sleep(10)

                print(f"Waiting {check_interval} seconds until next check...")
            except KeyboardInterrupt:
                print("\nCrawler stopped by user")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Continuing in 60 seconds...")

            # LOG
            if self.last_log_time + 3600 < time.time():
                with open("monitorbot.log", "a") as f:
                    f.write(f"# Last log time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --- {self.request_count} Submitted\n")
                self.last_log_time = time.time()

            time.sleep(check_interval)


def main():
    # Configuration - Replace these with your actual values
    CHANNEL_LIST = {
        '1220504695404236800': "β・dsperse・2",
        '1222226314824777853': "γ・τemplar・3",
        '1161765008347254915': "∆・τargon・4",
        # 1368959417936252998: "ε・hone・5",
        # 1209554949449457705: "ζ・numinous・6",
    }
    # with open("channel_list_1.json", "r", encoding="utf-8") as f:
    #     CHANNEL_LIST = json.load(f)
    BOT_TOKEN = ""  # Your bot token
    WEBHOOK_URL = "https://discord.com/api/webhooks/144052851142951184/aGpF3B6znsX4noqvR5yyLBptvdhbGj4tp3SPbBmFWCFcwADFkmpGbuFLywqNENzGkck"  # Replace with your webhook URL

    # List of user IDs to monitor (from your output example)
    TARGET_USER_IDS = [
        "389189199514959893",  # const
        # "595372674121990144",  # adamw
        # "1209166548955041835",  # atel
    ]

    # Create and run crawler
    crawler = DiscordCrawler(
        channel_list=CHANNEL_LIST,
        bot_token=BOT_TOKEN,
        webhook_url=WEBHOOK_URL,
        target_user_ids=TARGET_USER_IDS
    )
    
    crawler.run(check_interval=60)  # Check every 60 seconds

if __name__ == "__main__":
    main()

