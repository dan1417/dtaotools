import os
import requests
import json
import time
import threading
import tweepy
from dotenv import load_dotenv
from datetime import datetime
import re
import json
import time


WEBHOOK_URL = "https://discord.com/api/webhooks/14440521142951184/aGpF3B6znstX4noqvR5yyLBptvdhbGj4tp3SPbBmFWCFcwADFkmpGbuFLywqNENzGkck"
USERS = []
try:
    with open("handles.txt", "r") as f:
        USERS = f.read().splitlines()
except FileNotFoundError:
    print("handles.txt not found")
    USERS = []

TWEETS_DIR = "tweets"

mapping_subnets_from_xhandlers = [
    {
        "handlers": ["wouterhar"],
        "keywords": "",
        "subnet_number": 18
    },
    {
        "handlers": ["QuasarModels"],
        "keywords": ["quasar"],
        "subnet_number": 24
    },
    {
        "handlers": ["IOTA_SN9", "MacrocosmosAI"],
        "keywords": ["quasar"],
        "subnet_number": 9
    },
    {
        "handlers": ["gradients_ai"],
        "keywords": ["gradients"],
        "subnet_number": 56
    },
    {
        "handlers": ["oroagents"],
        "keywords": ["quasar"],
        "subnet_number": 15
    },
    {
        "handlers": ["TrajectoryRL"],
        "keywords": ["quasar"],
        "subnet_number": 11
    },
    {
        "handlers": ["AndorranAi", "SwarmSubnet"],
        "keywords": ["swarm"],
        "subnet_number": 124
    },
    {
        "handlers": ["theminos_ai"],
        "keywords": [],
        "subnet_number": 107
    },
]


# Load environment variables
load_dotenv()

class TwitterBotX:
    def __init__(self):
        # Twitter API credentials
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        # Initialize the client
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
        
        # Load last seen timestamp
        self.last_seen_file = 'last_seen_x.json'
        self.last_seen_id = self.load_last_seen()

    def load_last_seen(self):
        """Load the last seen tweet ID from file"""
        try:
            if os.path.exists(self.last_seen_file):
                with open(self.last_seen_file, 'r') as f:
                    return f.read().strip()
            return None
        except Exception as e:
            print(f"Error loading last seen data: {e}")
            return None

    def save_last_seen(self, tweet_id):
        """Save the last seen tweet ID to file"""
        try:
            with open(self.last_seen_file, 'w') as f:
                f.write(str(tweet_id))
        except Exception as e:
            print(f"Error saving last seen data: {e}")
    
    def get_tweets_from_user(self, username, max_results=50, since_id=None):
        """Get tweets from a single user using search_recent_tweets"""
        print(f"Getting tweets from user: {username} since ID: {since_id}")
        try:
            tweets = self.client.get_users_tweets(
                id=username,
                max_results=max_results,
                since_id=since_id,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
            )
            if not tweets.data:
                print(f"No tweets found for const_reborn")
                return None
            # Process the tweets
            formatted_tweets = []
            for tweet in tweets.data:
                
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'username': "const_reborn",
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count']
                }
                formatted_tweets.append(tweet_data)
                
            return formatted_tweets
        except Exception as e:
            print(f"Error fetching tweets: {e}")
            return None


    def check_new_tweets_by_specific_users(self, callback, interval=1):
        """Check for new tweets periodically from multiple users"""
        while True:

            try:
                # Get the last seen tweet ID
                since_id = self.last_seen_id
                
                # Fetch new tweets for all users
                new_tweets = self.get_tweets_from_user(1626325301432135684, max_results=50, since_id=since_id)
                if new_tweets:
                    # Update last seen ID with the most recent tweet
                    self.last_seen_id = new_tweets[0]['id']
                    self.save_last_seen(self.last_seen_id)
                    # Process new tweets in reverse order
                    for tweet in reversed(new_tweets):
                        callback(tweet)
                    
            except Exception as e:
                print(f"Error in check_new_tweets: {e}")
            time.sleep(interval)

def make_tweet_dir():
    if not os.path.exists(TWEETS_DIR):
        os.makedirs(TWEETS_DIR)


def send_message(content):
    data = {
        "content": content,
        "username": "X events",  # Optional: Custom username for the webhook
        "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
    }
    response = requests.post(WEBHOOK_URL, data=json.dumps(data), headers={"Content-Type": "application/json"})
    
    if response.status_code == 204:
        print("Message sent successfully!")
        return True
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")
    return False


def format_tweet(tweet):
    # Format the timestamp
    created_at = tweet['created_at']
    # Create a beautiful formatted message
    message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Hey @everyone!

🐦 ** {tweet['username']} ** 🐦
⏰ **Time:** {created_at}

{tweet['text']}

🔗 **Link:** https://x.com/{tweet['username']}/status/{tweet['id']}
"""  
    return message


def periodic_check(interval=1):

    while True:
        tweet_files = sorted(os.listdir(TWEETS_DIR), key=lambda x: int(x.split('.')[0]))
        for tweet_file_name in tweet_files:
            with open(f"{TWEETS_DIR}/{tweet_file_name}", 'r') as f:
                tweet = json.load(f)
                message = format_tweet(tweet)   
                result = send_message(message)
                if result:
                    os.remove(f"{TWEETS_DIR}/{tweet_file_name}")
                else:
                    break
        time.sleep(interval)


def callback(tweet):
    try:
        filename = f"{TWEETS_DIR}/{tweet['id']}.json"
        with open(filename, 'w') as f:
            json.dump(tweet, f, indent=4, default=str)
        print(f"Saved tweet {tweet['id']} to {filename}")
    except Exception as e:
        print(f"Error saving tweet {tweet['id']}: {e}")


def run_periodic_check():
    make_tweet_dir()
    check_thread = threading.Thread(target=periodic_check)
    check_thread.daemon = True
    check_thread.start()

def detect_subnets(tweet_text: str) -> list[int]:
    text_lower = tweet_text.lower()
    
    keyword_matches = []
    default_matches = []
    
    for entry in mapping_subnets_from_xhandlers:
        handlers = [h.lower() for h in entry["handlers"]]
        
        handler_hit = (any(f"@{h}" in text_lower for h in handlers))
        if not handler_hit:
            continue
        
        keywords = entry["keywords"] or []
        if keywords:
            if any(kw.lower() in text_lower for kw in keywords):
                keyword_matches.append(entry["subnet_number"])
        else:
            default_matches.append(entry["subnet_number"])
    
    return default_matches or keyword_matches


def main():
    run_periodic_check()
    bot = TwitterBotX()
    bot.check_new_tweets_by_specific_users(callback)


if __name__ == "__main__":
    main()
