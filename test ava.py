import json
from web3 import Web3
import time

# enter your amount to bridge
AMOUNT_TO_SWAP = 18  # 20 = 20 USDC

# enter slippage as shown => 1 = 0.1%, 5 = 0.5%, 10 = 1%
SLIPPAGE = 1

# put your private key here
PRIVATE_KEY = 'xxx'

# times to swap = > polygon -> fantom -> polygon = 1 time
TIMES = 49


# RPCs
polygon_rpc_url = 'https://polygon-rpc.com/'
fantom_rpc_url = 'https://1rpc.io/avax/c'

polygon_w3 = Web3(Web3.HTTPProvider(polygon_rpc_url))
fantom_w3 = Web3(Web3.HTTPProvider(fantom_rpc_url))

# Stargate Router
stargate_polygon_address = polygon_w3.to_checksum_address('0x45A01E4e04F14f7A4a6702c74187c5F6222033cd')
stargate_fantom_address = fantom_w3.to_checksum_address('0x45A01E4e04F14f7A4a6702c74187c5F6222033cd')

# ABIs
stargate_abi = json.load(open('router_abi.json'))
usdc_abi = json.load(open('usdc_abi.json'))

# USDC contracts
usdc_polygon_address = polygon_w3.to_checksum_address('0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174')
usdc_fantom_address = fantom_w3.to_checksum_address('0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E')

# Init contracts
stargate_polygon_contract = polygon_w3.eth.contract(address=stargate_polygon_address, abi=stargate_abi)
stargate_fantom_contract = fantom_w3.eth.contract(address=stargate_fantom_address, abi=stargate_abi)
usdc_polygon_contract = polygon_w3.eth.contract(address=usdc_polygon_address, abi=usdc_abi)
usdc_fantom_contract = fantom_w3.eth.contract(address=usdc_fantom_address, abi=usdc_abi)


# Polygon -> Fantom USDC Bridge
def swap_usdc_polygon_to_fantom(amount, min_amount):
    account = polygon_w3.eth.account.from_key(PRIVATE_KEY)
    address = account.address
    nonce = polygon_w3.eth.get_transaction_count(address)
    gas_price = polygon_w3.eth.gas_price
    fees = stargate_fantom_contract.functions.quoteLayerZeroFee(106,
                                                                1,
                                                                "0x0000000000000000000000000000000000001010",
                                                                "0x",
                                                                [0, 0, "0x0000000000000000000000000000000000000001"]
                                                                ).call()
    fee = fees[0]

    # Check allowance
    allowance = usdc_polygon_contract.functions.allowance(address, stargate_polygon_address).call()
    if allowance < amount:
        approve_txn = usdc_polygon_contract.functions.approve(stargate_polygon_address, amount).build_transaction({
            'from': address,
            'gas': 150000,
            'gasPrice': gas_price,
            'nonce': nonce,
        })
        signed_approve_txn = polygon_w3.eth.account.sign_transaction(approve_txn, PRIVATE_KEY)
        approve_txn_hash = polygon_w3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)

        print(f"POLYGON | USDT APPROVED https://polygonscan.com/tx/{approve_txn_hash.hex()}")
        nonce += 1

        time.sleep(50)

    usdc_balance = usdc_polygon_contract.functions.balanceOf(address).call()

    if usdc_balance >= amount:

        # Stargate Swap
        chainId = 106
        source_pool_id = 1
        dest_pool_id = 1
        refund_address = account.address
        amountIn = amount
        amountOutMin = min_amount
        lzTxObj = [0, 0, '0x0000000000000000000000000000000000000001']
        to = account.address
        data = '0x'

        swap_txn = stargate_polygon_contract.functions.swap(
            chainId, source_pool_id, dest_pool_id, refund_address, amountIn, amountOutMin, lzTxObj, to, data
        ).build_transaction({
            'from': address,
            'value': fee,
            'gas': 500000,
            'gasPrice': polygon_w3.eth.gas_price,
            'nonce': polygon_w3.eth.get_transaction_count(address),
        })

        signed_swap_txn = polygon_w3.eth.account.sign_transaction(swap_txn, PRIVATE_KEY)
        swap_txn_hash = polygon_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
        return swap_txn_hash

    elif usdc_balance < amount:

        min_amount = usdc_balance - (usdc_balance * 5) // 1000

        # Stargate Swap
        chainId = 106
        source_pool_id = 1
        dest_pool_id = 1
        refund_address = account.address
        amountIn = usdc_balance
        amountOutMin = min_amount
        lzTxObj = [0, 0, '0x0000000000000000000000000000000000000001']
        to = account.address
        data = '0x'

        swap_txn = stargate_polygon_contract.functions.swap(
            chainId, source_pool_id, dest_pool_id, refund_address, amountIn, amountOutMin, lzTxObj, to, data
        ).build_transaction({
            'from': address,
            'value': fee,
            'gas': 500000,
            'gasPrice': polygon_w3.eth.gas_price,
            'nonce': polygon_w3.eth.get_transaction_count(address),
        })

        signed_swap_txn = polygon_w3.eth.account.sign_transaction(swap_txn, PRIVATE_KEY)
        swap_txn_hash = polygon_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
        return swap_txn_hash



# Fantom -> Polygon USDC
def swap_usdc_fantom_to_polygon(amount, min_amount):
    account = fantom_w3.eth.account.from_key(PRIVATE_KEY)
    address = account.address
    nonce = fantom_w3.eth.get_transaction_count(address)
    gas_price = fantom_w3.eth.gas_price
    fees = stargate_fantom_contract.functions.quoteLayerZeroFee(109,
                                                       1,
                                                       "0x0000000000000000000000000000000000000001",
                                                       "0x",
                                                       [0, 0, "0x0000000000000000000000000000000000000001"]
                                                       ).call()
    fee = fees[0]

    # Check Allowance
    allowance = usdc_fantom_contract.functions.allowance(address, stargate_fantom_address).call()
    if allowance < amount:
        approve_txn = usdc_fantom_contract.functions.approve(stargate_fantom_address, amount).build_transaction({
            'from': address,
            'gas': 150000,
            'gasPrice': gas_price,
            'nonce': nonce,
        })
        signed_approve_txn = fantom_w3.eth.account.sign_transaction(approve_txn, PRIVATE_KEY)
        approve_txn_hash = fantom_w3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)

        print(f"FANTOM | USDC APPROVED | https://ftmscan.com/tx/{approve_txn_hash.hex()} ")
        nonce += 1

        time.sleep(50)

    usdc_balance = usdc_fantom_contract.functions.balanceOf(address).call()

    if usdc_balance >= amount:

        # Stargate Swap
        chainId = 109
        source_pool_id = 1
        dest_pool_id = 1
        refund_address = account.address
        amountIn = amount
        amountOutMin = min_amount
        lzTxObj = [0, 0, '0x0000000000000000000000000000000000000001']
        to = account.address
        data = '0x'

        swap_txn = stargate_fantom_contract.functions.swap(
            chainId, source_pool_id, dest_pool_id, refund_address, amountIn, amountOutMin, lzTxObj, to, data
        ).build_transaction({
            'from': address,
            'value': fee,
            'gas': 600000,
            'gasPrice': fantom_w3.eth.gas_price,
            'nonce': fantom_w3.eth.get_transaction_count(address),
        })

        signed_swap_txn = fantom_w3.eth.account.sign_transaction(swap_txn, PRIVATE_KEY)
        swap_txn_hash = fantom_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
        return swap_txn_hash

    elif usdc_balance < amount:

        min_amount = usdc_balance - (usdc_balance * 5) // 1000

        # Stargate Swap
        chainId = 109
        source_pool_id = 1
        dest_pool_id = 1
        refund_address = account.address
        amountIn = usdc_balance
        amountOutMin = min_amount
        lzTxObj = [0, 0, '0x0000000000000000000000000000000000000001']
        to = account.address
        data = '0x'

        swap_txn = stargate_fantom_contract.functions.swap(
            chainId, source_pool_id, dest_pool_id, refund_address, amountIn, amountOutMin, lzTxObj, to, data
        ).build_transaction({
            'from': address,
            'value': fee,
            'gas': 600000,
            'gasPrice': fantom_w3.eth.gas_price,
            'nonce': fantom_w3.eth.get_transaction_count(address),
        })

        signed_swap_txn = fantom_w3.eth.account.sign_transaction(swap_txn, PRIVATE_KEY)
        swap_txn_hash = fantom_w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)
        return swap_txn_hash


def main():
    counter = 0
    slippage = SLIPPAGE
    amount_to_swap = AMOUNT_TO_SWAP * (10 ** 6)
    min_amount = amount_to_swap - (amount_to_swap * slippage) // 1000

    while counter < TIMES:
        print("Swapping USDC from Polygon to Fantom...")
        polygon_to_fantom_txn_hash = swap_usdc_polygon_to_fantom(amount_to_swap, min_amount)
        print(f"Transaction: https://polygonscan.com/tx/{polygon_to_fantom_txn_hash.hex()}")

        print("Waiting for the swap to complete...")
        time.sleep(1500)

        print("Swapping USDC from Fantom to Polygon...")
        fantom_to_polygon_txn_hash = swap_usdc_fantom_to_polygon(amount_to_swap, min_amount)
        print(f"Transaction: https://ftmscan.com/tx/{fantom_to_polygon_txn_hash.hex()}")

        print("Waiting for the swap to complete...")
        time.sleep(160)

        counter += 1

    print(f'***** JOB IS OVER *****')


if __name__ == '__main__':
    main()
