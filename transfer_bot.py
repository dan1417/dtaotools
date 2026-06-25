import bittensor as bt
import os
import requests
import json
import time
import threading
import requests

import re

WEBHOOK_URL = "https://discord.com/api/webhooks/1460346222127878217/I827saoZJTVmZW7JgZZyBFg6JK-qd7-6a8uAah5FP9jpCTwMiiwFNUQQDkBcAWeq0T6K"
NETWORK = "finney"
#NETWORK = "ws://34.30.248.57:9944"
REFRESH_INTERVAL = 20 # minutes

class DiscordBot:
    def __init__(self):
        self.webhook_url = WEBHOOK_URL

    def send_webhook_url(self, message):
        embeds = {
            "title": f"🚩Tao Transfer Alert",
            "description": f"**{message}**",
            "color": 0xff0000
        }
        print(f"Sending embeds: {embeds}")
        payload = {
            "content": None,
            "username": "Transfer Bot",
            "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico",  # Optional: Custom avatar for the webhook
            "embeds": [embeds]
        }
        
        retries = 20
        while retries > 0:
            try:
                response = requests.post(self.webhook_url, json=payload)
                if response.status_code in [200, 204]:
                    print(f"Successfully sent {len(embeds)} message(s) to webhook")
                    break
                else:
                    print(f"Failed to send webhook: {response.status_code} {response.text}")
            except Exception as e:
                print(f"Error sending webhook: {e}")
            retries -= 1

    def send_message(self, content):
        data = {
            "content": content,
            "username": "Coldkey Swap Bot",  # Optional: Custom username for the webhook
            "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
        }
        response = requests.post(self.webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})

        if response.status_code == 204:
            print("Message sent successfully!")
            return True
        else:
            print(f"Failed to send message: {response.status_code}, {response.text}")
        return False

class TransferFetcher:

    def __init__(self):
        self.subtensor = bt.Subtensor(NETWORK)

        self.bots = []
        self.wallet_owners = {}
        self.owner_coldkeys = []
        self.last_checked_block = self.subtensor.get_current_block()
        self.discord_bot = DiscordBot()
        # start periodic refresh
        self.refresh_bots_periodically()
        self.refresh_owner_coldkeys_periodically()

    # -----------------------------|
    #       Google Docs loaders    |
    # -----------------------------|
    def load_bots_from_gdoc(self):
        url = "https://docs.google.com/document/d/1Vdm20cXVAK-kjgjBw9XcbVYaAvvCWyY8IuPLAE2aRBI/export?format=txt"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            text = response.text
            self.bots = re.findall(r'5[1-9A-HJ-NP-Za-km-z]{47}', text)
        except Exception as e:
            print(f"Failed to load bots from Google Doc: {e}")
            
    def load_wallet_owners_from_gdoc(self):
        urls = [
            "https://docs.google.com/document/d/181kjUmksmtS8aXTV7LC0JMcdbHy0f2ClHORBYM-pek0/export?format=txt",
        ]
        for url in urls:    
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                text = response.text
                # Each pair is like: <wallet_address> <owner_name>
                # build a dict mapping wallet address to owner name
                pattern = r'(5[1-9A-HJ-NP-Za-km-z]{47})\s+([^\s]+)'
                for address, owner in re.findall(pattern, text):
                    self.wallet_owners[address] = owner

            except Exception as e:
                print(f"Failed to load wallet owners from Google Doc: {e}")

    # -----------------------------|
    #       Periodic refreshers    |
    # -----------------------------|
            
    def refresh_bots_periodically(self, interval_minutes=REFRESH_INTERVAL):
        self.load_wallet_owners_from_gdoc()
        self.load_bots_from_gdoc()
        threading.Timer(interval_minutes * 60, self.refresh_bots_periodically, [interval_minutes]).start()

    def refresh_owner_coldkeys_periodically(self, interval_minutes=REFRESH_INTERVAL):
        subnet_infos = self.subtensor.all_subnets()
        self.owner_coldkeys = [subnet_info.owner_coldkey for subnet_info in subnet_infos]
        threading.Timer(interval_minutes * 60, self.refresh_owner_coldkeys_periodically, [interval_minutes]).start()

    # -----------------------------|
    #       Display helpers        |
    # -----------------------------|

    def get_coldkey_display_name(self, coldkey):
        if coldkey is None:
            return "Unknown"
        owner_color = "\033[93m"
        color = "\033[95m"
        reset = "\033[0m" 

        if coldkey in self.owner_coldkeys:
            return coldkey + f"{owner_color} (owner{self.owner_coldkeys.index(coldkey)}){reset}"

        if coldkey in self.bots:
            return coldkey + f"{color} (bot{self.bots.index(coldkey)+1}){reset}"
        

        if coldkey in self.wallet_owners:
            return coldkey + f"{owner_color} ({self.wallet_owners[coldkey]}){reset}"
        
        return coldkey

    def get_color(self, event_type):
        if event_type == 'StakeAdded':
            return "\033[92m"
        elif event_type == 'StakeRemoved':
            return "\033[91m"
        else:
            return "\033[0m"


    def extract_stake_transfer_events_from_data(self, events_data):
        """
        Extract stake and unstake events from blockchain event data.
        
        Args:
            events_data: List of event dictionaries from blockchain
        
        Returns:
            List of dictionaries containing stake/unstake event information
        """
        stake_events = []
        transfer_events = []
        
        for event in events_data:
            event_info = event.get('event', {})
            # Convert coldkey and hotkey to ss58 addresses if possible      
            if event_info.get('module_id') == 'Balances':
                event_id = event_info.get('event_id')
                attributes = event_info.get('attributes', {})
                if event_id == 'Transfer':
                    from_address, to_address, amount = attributes['from'], attributes['to'], attributes['amount'] / 1e9  
                    transfer_events.append({
                        'type': 'Transfer',
                        'from': from_address,
                        'to': to_address,
                        'amount': amount,
                    })
               
        return stake_events, transfer_events
    
    # -----------------------------|
    #           Printers           |
    # -----------------------------|
    def print_transfer_events(self, transfer_events):
        color = "\033[92m"
        reset = "\033[0m"
        for event in transfer_events:
            tao_amount = event['amount']
            from_addr = event['from']
            to_addr = event['to']
            print(f"{color}{from_addr} => {to_addr}  {tao_amount:5.2f} {reset}")

    def format_address(self, coldkey):
        if coldkey in self.wallet_owners and self.wallet_owners[coldkey] != "jeeter":
            return f"**{self.wallet_owners[coldkey]}**({coldkey})"
        elif coldkey in self.owner_coldkeys:
            return f"**SN {self.owner_coldkeys.index[coldkey] + 1} Owner**({coldkey})"
        else:
            return f"unknown({coldkey})"

    def convert_message(self, from_addr, to_addr, tao_amount):
        src = self.format_address(from_addr)
        dst = self.format_address(to_addr)
        flag = False

        if not "unknown" in src or not "unknown" in dst :
            flag = True

        message = f"Hey @everyone! \n💢 {src} => {dst} **** {tao_amount}\n"
        
        return message, flag
    
    def run(self):    

        while True:
            block_number = self.subtensor.get_current_block()
            block_hash = self.subtensor.substrate.get_block_hash(block_id=block_number)
            events = self.subtensor.substrate.get_events(block_hash=block_hash)

            
            # Extract stake events from live data
            print(f"*{'*'*40}")
            _, transfer_events = self.extract_stake_transfer_events_from_data(events)
            # if stake_events:
            #     print(f"*{'*'*40}")
            #     print_stake_events(stake_events, netuid, show_balance)

            if transfer_events:
                
                self.print_transfer_events(transfer_events)
                try:
                    color = "\033[92m"
                    reset = "\033[0m"
                    for event in transfer_events:
                        tao_amount = event['amount']
                        from_addr = event['from']
                        to_addr = event['to']
                        print(f"{color}{from_addr} => {to_addr}  {tao_amount:5.2f} {reset}")
                        message, flag = self.convert_message(from_addr, to_addr, tao_amount)
                        if flag == True:
                            self.discord_bot.send_webhook_url(message)
                except Exception as e:
                    print(f"Error sending message: {e}")
            self.subtensor.wait_for_block()

if __name__ == "__main__":
    fetcher = TransferFetcher()
    fetcher.run()
