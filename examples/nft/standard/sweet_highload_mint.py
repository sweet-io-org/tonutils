from pytoniq_core import Address
import uuid

from typing import Union
from tonutils.client import TonapiClient
from tonutils.nft.content import SweetOffchainContent
from tonutils.nft.contract.standard.collection import SweetCollectionStandard
from tonutils.nft.contract.standard.nft import SweetNFTStandard
from tonutils.wallet import WalletV5R1, HighloadWalletV3
from tonutils.wallet.data import TransferData


# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet, should be minter or owner of the NFT collection
MNEMONIC: list[str] = []

# Address of the destination owners of the NFT
OWNER_ADDRESS_1 = ""
OWNER_ADDRESS_2 = ""

COLLECTION_ADDRESS = ""


def uuid_to_query_id(txn_id: Union[str, uuid.UUID]) -> int:
    if isinstance(txn_id, str):
        txn_id = uuid.UUID(txn_id)
    return txn_id.int & 0xFFFFFFFFFFFFFFFF  # Use lower 64 bits for query_id

async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = HighloadWalletV3.from_mnemonic(client, MNEMONIC)

    nft = SweetNFTStandard(
        collection_address=Address(COLLECTION_ADDRESS),
    )
    body_1 = SweetCollectionStandard.build_mint_body(
        owner_address=Address(OWNER_ADDRESS_1),
        query_id=uuid_to_query_id(uuid.uuid4())
    )

    body_2 = SweetCollectionStandard.build_mint_body(
        owner_address=Address(OWNER_ADDRESS_2),
        query_id=uuid_to_query_id(uuid.uuid4())
    )

    datalist =[]

    datalist.append(TransferData(destination=COLLECTION_ADDRESS, amount=0.02, body=body_2))
    datalist.append(TransferData(destination=COLLECTION_ADDRESS, amount=0.02, body=body_1))


    tx_hash = await wallet.batch_transfer(datalist)

    print(f"Successfully minted NFT from collection {nft.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
