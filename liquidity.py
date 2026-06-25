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
    netuid = int(input("Enter the netuid: "))
    
#    limit = int(input("Enter the limit: "))
    limit = 1
    subtensor = bt.Subtensor(network=NETWORK)
    prev_tao_in = 0
    prev_price = 0
    try:
        while True:
            try:
                subnet = subtensor.subnet(netuid=netuid)
                if subnet is None:
                    print(f"Subnet is None for netuid: {netuid}")
                    continue
                
                price = subnet.alpha_to_tao(1)
                now_tao_in = subnet.tao_in
                price_now = subnet.price
                if now_tao_in is None:
                    print(f"Now tao in is None for netuid: {netuid}")
                    continue
                tao_flow = now_tao_in - prev_tao_in
                if tao_flow.tao > limit:
                    print(f"\n+ UID: {netuid} => Price: {price.tao:.5f}, Flow: {tao_flow.tao:.2f} => {price_now.tao:.5f}")
                elif -1*tao_flow.tao > limit:
                    print(f"\n- UID: {netuid} => Price: {price.tao:.5f}, Flow: {tao_flow.tao:.2f} => {price_now.tao:.5f}")
                else:
                    print(f"UID: {netuid} => Price: {price.tao:.5f}, Flow: {tao_flow.tao:.2f}")
                prev_tao_in = now_tao_in
                subtensor.wait_for_block()
            except Exception as e:
                print(f"Error in watching_price: {e}")
                continue
    except KeyboardInterrupt:
        print("Program interrupted. Exiting...")
        exit(0)
