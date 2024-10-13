from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, Dict, List, Optional

from pytoniq_core import Address, SimpleAccount

from ..account import AccountStatus, RawAccount
from ..exceptions import PytoniqDependencyError

try:
    # noinspection PyPackageRequirements
    from pytoniq import LiteBalancer

    pytoniq_available = True
except ImportError:
    pytoniq_available = False
    from ._base import LiteBalancer

from ._base import Client


def require_pytoniq(func) -> Callable:
    """
    Decorator to ensure that the pytoniq library is available and the client is initialized.
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not pytoniq_available:
            raise PytoniqDependencyError()
        await self.initialize_client()
        return await func(self, *args, **kwargs)

    return wrapper


class LiteserverClient(Client):
    """
    LiteClient class for interacting with the TON blockchain using LiteserverClient.

    This class provides methods to run get methods and send messages to the blockchain,
    with options for configuration and network selection.
    """

    def __init__(
            self,
            config: Optional[Dict[str, Any]] = None,
            is_testnet: bool = False,
            trust_level: int = 2,
    ) -> None:
        """
        Initialize the LiteClient.

        :param config: The configuration dictionary for LiteBalancer. Defaults to None.
            You can pass your own config from a private lite server,
            which can be acquired from the https://t.me/liteserver_bot.
        :param is_testnet: Flag to indicate if testnet configuration should be used. Defaults to False.
        :param trust_level: The trust level for the LiteBalancer.
            Defines the level of trust for Liteserver communication. Defaults to 2.
            For trustless communication with Lite servers, there are "Proofs" in TON. The trust_level argument
            in the LiteClient constructor defines how much you trust the Liteserver you communicate with.
            Refer to the documentation for more details: https://yungwine.gitbook.io/pytoniq-doc/liteclient/trust-levels
        """
        super().__init__()

        if not pytoniq_available:
            raise PytoniqDependencyError()

        self.client = self._get_lite_balancer(config, is_testnet, trust_level)

    @staticmethod
    def _get_lite_balancer(config: Optional[Dict[str, Any]], is_testnet: bool, trust_level: int) -> LiteBalancer:
        if config:
            return LiteBalancer.from_config(config=config, trust_level=trust_level)
        elif is_testnet:
            return LiteBalancer.from_testnet_config(trust_level=trust_level)
        return LiteBalancer.from_mainnet_config(trust_level=trust_level)

    async def initialize_client(self) -> None:
        if not self.client.inited:
            await self.client.start_up()

    async def close_client(self) -> None:
        if self.client.inited:
            await self.client.close_all()

    @require_pytoniq
    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        return await self.client.run_get_method(address, method_name, stack or [])

    @require_pytoniq
    async def send_message(self, boc: str) -> None:
        return await self.client.raw_send_message(bytes.fromhex(boc))

    @require_pytoniq
    async def get_raw_account(self, address: str) -> RawAccount:
        address = Address(address)
        account, shard_account = await self.client.raw_get_account_state(address)
        simple_account = SimpleAccount.from_raw(account, address)

        status = (
            "uninit"
            if simple_account.state.type_ == "uninitialized" else
            simple_account.state.type_
        )

        return RawAccount(
            balance=int(simple_account.balance),
            code=simple_account.state.state_init.code,
            data=simple_account.state.state_init.data,
            status=AccountStatus(status),
            last_transaction_lt=shard_account.last_trans_lt,
            last_transaction_hash=shard_account.last_trans_hash.hex(),
        )

    @require_pytoniq
    async def get_account_balance(self, address: str) -> int:
        raw_account = await self.get_raw_account(address)
        return raw_account.balance
