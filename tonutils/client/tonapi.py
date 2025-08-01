from typing import Any, List, Optional

from pytoniq_core import Cell

from ..account import AccountStatus, RawAccount
from ._base import Client
from .models import Transaction, TransactionReceipt


class TonapiClient(Client):
    """
    TonapiClient class for interacting with the TON blockchain.

    This class provides methods to run get methods and send messages to the blockchain,
    with options for network selection.
    """

    def __init__(
        self,
        api_key: str,
        is_testnet: Optional[bool] = False,
        base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize the TonapiClient.

        :param api_key: The API key for accessing the Tonapi service.
            You can get API key here: https://tonconsole.com.
        :param is_testnet: Flag to indicate if testnet configuration should be used. Defaults to False.
        :param base_url: Optional base URL for the Tonapi service. If not provided,
            the default public URL will be used. You can specify your own API URL if needed.
        """
        if base_url is None:
            base_url = (
                "https://tonapi.io" if not is_testnet else "https://testnet.tonapi.io"
            )
        headers = {"Authorization": f"Bearer {api_key}"}

        super().__init__(base_url=base_url, headers=headers, is_testnet=is_testnet)

    async def run_get_method(
        self,
        address: str,
        method_name: str,
        stack: Optional[List[Any]] = None,
    ) -> Any:
        method = f"/v2/blockchain/accounts/{address}/methods/{method_name}"

        if stack:
            query_params = "&".join(f"args={arg}" for arg in stack)
            method = f"{method}?{query_params}"

        return await self._get(method=method)

    async def send_message(self, boc: str) -> None:
        method = "/v2/blockchain/message"

        await self._post(method=method, body={"boc": boc})

    async def get_raw_account(self, address: str) -> RawAccount:
        method = f"/v2/blockchain/accounts/{address}"
        result = await self._get(method=method)

        code = result.get("code")
        code_cell = Cell.one_from_boc(code) if code else None
        data = result.get("data")
        data_cell = Cell.one_from_boc(data) if data else None
        _lt, _lt_hash = result.get("last_transaction_lt"), result.get(
            "last_transaction_hash"
        )
        lt, lt_hash = int(_lt) if _lt else None, _lt_hash if _lt_hash else None

        return RawAccount(
            balance=int(result.get("balance", 0)),
            code=code_cell,
            data=data_cell,
            status=AccountStatus(result.get("status", "uninit")),  # noqa
            last_transaction_lt=lt,
            last_transaction_hash=lt_hash,
        )

    async def get_account_balance(self, address: str) -> int:
        raw_account = await self.get_raw_account(address)

        return raw_account.balance

    async def get_block_hash(self, block_id: str) -> None:
        method = f"/v2/blockchain/blocks/{block_id}"
        try:
            block = await self._get(method=method)
        except Exception as e:
            if "not found" in str(e):
                return None
        if block:
            return block.get("root_hash")
        return None

    async def get_transaction(self, address: str, hash: str) -> TransactionReceipt:
        method = f"/v2/blockchain/transactions/{hash}"
        try:
            result = await self._get(method=method)
        except Exception as e:
            if "not found" in str(e):
                return None
        if result:
            root_txn = Transaction.from_ton_api_trace(result)
            block_hash = await self.get_block_hash(root_txn.block)
            return TransactionReceipt.from_transaction(root_txn, block_hash=block_hash)
        else:
            return None

    async def get_collection(self, collection: str) -> dict:
        """
        Retrieve collection from the blockchain.
        """
        method = f"/v2/nfts/collections/{collection}"
        return await self._get(method=method)

    async def get_collections(self, collections: List[str]) -> dict:
        """
        Retrieve collections from the blockchain.
        """
        method = "/v2/nfts/collections/_bulk"
        result = await self._post(method=method, body={"account_ids": collections})
        return result["nft_collections"]

    async def trace_transaction(self, txn_hash: str) -> TransactionReceipt:
        method = f"/v2/traces/{txn_hash}"
        try:
            result = await self._get(method=method)
        except Exception as e:
            if "not found" in str(e):
                return None
        if result:
            root_txn = Transaction.from_ton_api_trace(result)
            block_hash = await self.get_block_hash(root_txn.block)
            return TransactionReceipt.from_transaction(root_txn, block_hash=block_hash)
        else:
            return None
