import sys
import os

# Add the parent directory to the Python search path (sys.path)
# parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# if parent_dir not in sys.path:
#     sys.path.insert(0, parent_dir)
    
import bittensor as bt
# from app.constants import NETWORK
# from utils.logger import logger

NETWORK = 'finney'
if __name__ == '__main__':
    netuid = 120 # affine netuid 
    subtensor = bt.subtensor(network=NETWORK)
    metagraph = subtensor.metagraph(netuid=120)
    emissions = metagraph.E.tolist()
    coldkeys = metagraph.coldkeys
    price = subtensor.subnet(netuid=120).alpha_to_tao(1)
    
    top_miner_emission = max(emissions)
    top_miner_uid = emissions.index(top_miner_emission)
    print(f"Top miner uid: {top_miner_uid}")
    print(f"Top miner daily tao: {top_miner_emission*20*price} tao")
    print(f"Top miner coldkey: {coldkeys[top_miner_uid]}\n\n")
    
    if coldkeys[top_miner_uid] == "5Fc3ZZQAYB3SPXKcFnd1WJeyQvArSZZeB6LU1rb7zvQ6XvDh":
        print("\033[31mIts const\033[0m\n")
    else:
        print("\033[32mIt's unconst. Let's unstake guys\033[0m\n")

