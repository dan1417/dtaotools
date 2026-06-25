import bittensor as bt
import time
from fastapi import FastAPI
import argparse

app = FastAPI()

name_s58_emission_rank_old = {}
name_s58_emission_rank_new = {}
result = {}
hotkey_list = {
'targon-h1' : '5EehXgq1GzGuafytc7shq3x3WmEQwVsmSFxWoqREzR3V38sD', 
'targon-h2' : '5CoHx59qWgY7FBYe3K6FnP2a2jiSuGf4dA3JEYC5XMSvhxZT', 
'targon-h3' : '5GWLgraYhGwD4UcwRZbEu5WbKpiHzbBzmh9c5578ky8HqCkr', 
'targon-h4' : '5HYpbhm1zeT7ktcpjPMekhD8zyZtvs5iDc4YZeucSqmy76Fa', 
'targon-h5' : '5D2UsRm1Axc1ktgDbEpD1mzigMkiyEAjPy4MpyhHJEK7gzKc', 
'targon-h6' : '5DAKk4Ex49k2ivyyoLjgXMfbYGk44Pr1dm5mjA8u3za52XQd', 
'targon-h7' : '5CGRreK4WuH8jnrzSKu1dh61JospVRK7iaF7MG6evYg1cEGJ', 
'targon-h8' : '5EHNmpMH6EutPnMe6qKoYhjW3u34tdhnRbZKLS2hdSs9gEnd', 
'targon-h9' : '5EACXC5VkbnVmi2ESv3znBLrqrmCBfH13QrV9Xumpbp7Peii', 
'targon-h10' : '5DnUczuVh3wfPBTW2PY7L5a6FGQR6JAvfmrbr7BGANdN9vAo', 
'targon-h11' : '5FBrVnj6cKrycTWGK3dqV73f2EuZMwKNBtDvoWFgNDtPcdpw', 
'targon-h12' : '5HBaracbLDL8Da2Fj5m53eBoqsFi9KWzAX86hxrUrACugMQp', 
'targon-h13' : '5G23ZbuguhLqHUrWS51JL2pGYHhs3f4TmaQeEiK3dWfmKH1B', 
'targon-h14' : '5HVopRUpGnstiUPwj7HWDcU34m3zF3bHUAM1to6ZMFqicB3v', 
'targon-h15' : '5FTWZkPRFsxtnWpjPU34rZqSymrDpv9a6XZosHXEA4mXveLW', 
'targon-h16' : '5Ehaa2SuMvpyik1RQonate1Kd2htEEbw7TWtLbdVZFpnjccQ', 
'targon-h17' : '5F6RAa5rQcoxPd35gR99VjUWYXsqnSqDo7BmG95R1oztWL2g', 
'targon-h18' : '5CVaFuVaun9etcyvUdaj1s9ZFouWA8DzTiprhnTEPa4CJJnf', 
'targon-h19' : '5GdrWsLsPt6ZRre1jAZav1JozrotV3TLQc7ChtsY7VigJBct', 
'targon-h20' : '5Fsqucky4z7DMpWMQJzm9AEHpRXGJfq5Y7jxgApfwFUUJfX4',

'targon2-h1' : '5GnMRreb1Etw9v82iDTifEdgr2tXL557ACRn7rv5qbWE3z4q', 
'targon2-h2' : '5C9zZfT7pns3TtfWVZZfG6UpYx5xrtRHtiby78tAZRhzEKDW', 
'targon2-h3' : '5Cvr1vpkWQkshihc3WbbjnBXCQHzgeQPjRpaQ9Xttniu3kkV', 
'targon2-h4' : '5GirsyY4Lw6Ui7N4HwXirPm3FjfK8x79gBnmsct7ncwY25MY', 
'targon2-h5' : '5H3aNfxruKpBHzt52F9Tn4jjDifgv2mnHKLQ3T3B4xeVj3JZ', 
'targon2-h6' : '5HgPM7GSZc6ntwRpemjRfnyNh7rfut81vr75V3oPBz2u8TrN', 
'targon2-h7' : '5E4c1krjwZRFsaUiYiQe4A8adrx1WMPBPsccaGwGWVyPswCH', 
'targon2-h8' : '5D7wSrQTzD8c4S7tZWYG1J1uitX6NnN23NBFfYjvJ37mZtMF', 
'targon2-h9' : '5DXCRT4MKRTyLPnRLXdx173whtssp5qFGvVaX3Ad3QBB11LR', 
'targon2-h10' : '5EcHyuhQGwHKYPYq6BMQa7QSWvR1kqZRwjhgJ9jPTTdEbAAw',

'targon3-h1' : '5D9nVoczqcrxAump2Nxghhv4PqpYnHYXVUduaVxKF6Ysjv1Y', 
'targon3-h2' : '5EEjkw7epWLs6umeEY1UdFVsjmt1ZJSVhr5dSLMehznnCpTw', 
'targon3-h3' : '5EemLYa94DLwmY35g6EfLTuahnf5iHvQULjhQp3UUPyb3Tok', 
'targon3-h4' : '5CCzdKkEwjVM62Bg8A4iShN9jtFpgZVRu2eQjE7VDGVHdp97', 
'targon3-h5' : '5ER9sud1G211x4iQfBpdSthMLWQG1TgbqHNfUdU4pN2iTde1', 
'targon3-h6' : '5Fga1TFLhb8jMjmdXnHMf9ZGRXp5Ktr939fxefSwNcchRdnD', 
'targon3-h7' : '5FJ2FqFmM3PKm5j7b3fEXWFMjVi5dqeL6W4EKvgpux5tVcXq', 
'targon3-h8' : '5ED8c684Nofm3Jw9fwjY5Z8NcJ5aecG1AZBVhbk6eDyr5Y8s', 
'targon3-h9' : '5CQK44qtXqZ7FjSfv3jXykBJXJZambs9pBVqzc2UjxsY3p7Z', 
'targon3-h10' : '5HMzhmwNbbLkLsrP7eiM6mk945VpCGaqYdphtzJQBQWXLxx9',
}

# @app.get("/")
# def show():
#     return "hello world"

# Function to find keys from hotkey list with corresponding indices in hotkeys
def find_keys_with_indices(hotkeys: list, hotkey_list: dict):
    result = {}
    for key, value in hotkey_list.items():
        if value in hotkeys:
            result[key] = hotkeys.index(value)
    return result

def fetch(netuid: int):
    global name_s58_emission_rank_old, name_s58_emission_rank_new, result

    metagraph = bt.subtensor('finney').metagraph(netuid=netuid)
    emissions = metagraph.E.tolist()
    hotkeys = metagraph.hotkeys

    hotkey2uid = find_keys_with_indices(hotkeys, hotkey_list)
  

    emission_ranks = []
    for emission in emissions:
        rank = sorted(emissions).index(emission) + 1
        emission_ranks.append([emission*20, rank])

    hotkey_emission_ranks = {}
    for i in range(len(emissions)):
        hotkey_emission_ranks[hotkeys[i]] = [emission_ranks[i][0], emission_ranks[i][1]]

    name_s58_emission_rank_new = {}
    for key, val in hotkey_list.items():
        if val in hotkey_emission_ranks:
            name_s58_emission_rank_new[key] = [val, hotkey_emission_ranks[val][0], hotkey_emission_ranks[val][1]]
    
    total_emission = 0
    print("Hotkey Name | Rank | Emission")
    for key, value in name_s58_emission_rank_new.items():
        print(f"{key} | {value[2]} | {value[1]}")
        total_emission+=value[1]

    result = {}
    t1cnt, t2cnt, t3cnt = 0, 0, 0
    for key, val in name_s58_emission_rank_new.items():
        if key.startswith("targon2"):
            t2cnt+=1
        elif key.startswith("targon3"):
            t3cnt+=1
        elif key.startswith("targon"):
            t1cnt+=1
        if key not in name_s58_emission_rank_old and name_s58_emission_rank_old!={}:
            print(f"New miner registered: {key}")
            result[key] = [name_s58_emission_rank_new[key][2], '-']    
            continue
    print(f"targon1 : {t1cnt}\ntargon2 : {t2cnt}\ntargon3 : {t3cnt}")
    print(f"Total emission: {total_emission} Tao/day")
    try:
        log_file = open('logs.txt', 'a')
    except FileNotFoundError:
        log_file = open('logs.txt', 'w')
    log_file.write('------------\n')
    log_file.write(str(result))
    log_file.close()
    name_s58_emission_rank_old = name_s58_emission_rank_new

if __name__ == '__main__':
    argp = argparse.ArgumentParser(description="config")
    argp.add_argument("--netuid", type=int, default=4)
    args  = argp.parse_args()
    netuid = args.netuid
    while True:
        fetch(netuid)
        time.sleep(600)
