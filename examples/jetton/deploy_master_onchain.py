from tonutils.client import TonapiClient
from tonutils.jetton import JettonMaster
from tonutils.jetton.content import JettonOnchainContent
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the administrator for managing the Jetton Master
ADMIN_ADDRESS = "UQ..."


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    jetton_master = JettonMaster(
        client=client,
        content=JettonOnchainContent(
            name="Ness Jetton",
            symbol="NESS",
            description="Probably nothing",
            decimals=9,
            image_data=b'image data',
        ),
        admin_address=ADMIN_ADDRESS,
    )

    tx_hash = await wallet.transfer(
        destination=jetton_master.address,
        amount=0.05,
        state_init=jetton_master.state_init,
    )

    print(f"Successfully deployed Jetton Master at address: {jetton_master.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
