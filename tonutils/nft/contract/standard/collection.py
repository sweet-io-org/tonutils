from __future__ import annotations

from typing import List, Optional, Tuple, Union

from pytoniq_core import Address, Cell, HashMap, begin_cell

from ...content import (
    CollectionModifiedOffchainContent,
    CollectionModifiedOnchainContent,
    CollectionOffchainContent,
    NFTModifiedOffchainContent,
    NFTModifiedOnchainContent,
    NFTOffchainContent,
    SweetOffchainContent,
)
from ...data import CollectionData
from ...op_codes import *
from ...royalty_params import RoyaltyParams
from ..base.collection import Collection, get_gas_fee
from .nft import NFTStandard


class CollectionStandardBase(Collection):
    def __init__(
        self,
        owner_address: Address,
        next_item_index: int,
        content: Union[
            CollectionOffchainContent,
            CollectionModifiedOnchainContent,
            CollectionModifiedOffchainContent,
            SweetOffchainContent,
        ],
        royalty_params: RoyaltyParams,
    ) -> None:
        self._data = self.create_data(
            owner_address, next_item_index, content, royalty_params
        ).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
        cls,
        owner_address: Address,
        next_item_index: int,
        content: Union[
            CollectionOffchainContent,
            CollectionModifiedOnchainContent,
            CollectionModifiedOffchainContent,
        ],
        royalty_params: RoyaltyParams,
    ) -> CollectionData:
        return CollectionData(
            owner_address=owner_address,
            next_item_index=next_item_index,
            content=content,
            royalty_params=royalty_params,
            nft_item_code=NFTStandard.CODE_HEX,
        )

    @classmethod
    def build_mint_body(
        cls,
        index: int,
        owner_address: Address,
        amount: int = 20000000,
        query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the mint transaction.

        :param index: The index of the nft to be minted.
        :param owner_address: The address of the owner.
        :param content: The content of the nft to be minted.
        :param amount: The amount of coins in nanoton. Defaults to 20000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the mint transaction.
        """
        return (
            begin_cell()
            .store_uint(NFT_MINT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_uint(index, 64)
            .store_coins(amount)
            .store_ref(begin_cell().store_address(owner_address).end_cell())
            .end_cell()
        )

    @classmethod
    def build_batch_mint_body(
        cls,
        data: List[
            Tuple[
                Union[
                    NFTOffchainContent,
                    NFTModifiedOnchainContent,
                    NFTModifiedOffchainContent,
                ],
                Address,
            ]
        ],
        from_index: int,
        amount_per_one: int = 20000000,
        query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the batch mint transaction.

        :param data: The list of data for minting. Each tuple contains:
            - OffchainCommonContent: The content of the nft to be minted.
            - Address: The address of the owner.
        :param from_index: The starting index for minting.
        :param amount_per_one: The amount of coins in nanoton per nft. Defaults to 20000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the batch mint transaction.
        """
        items_dict = HashMap(key_size=64)

        for i, (content, owner_address) in enumerate(data, start=0):
            items_dict.set_int_key(
                i + from_index,
                begin_cell()
                .store_coins(amount_per_one)
                .store_ref(
                    begin_cell()
                    .store_address(owner_address)
                    .store_ref(content.serialize())
                    .end_cell()
                )
                .end_cell(),
            )

        return (
            begin_cell()
            .store_uint(BATCH_NFT_MINT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_dict(items_dict.serialize())
            .end_cell()
        )


class CollectionStandard(CollectionStandardBase):
    CODE_HEX = "b5ee9c72410213010001fe000114ff00f4a413f4bcf2c80b0102016204020201200e030025bc82df6a2687d20699fea6a6a182de86a182c40202cd0a050201200706003d45af0047021f005778018c8cb0558cf165004fa0213cb6b12ccccc971fb0080201200908001b3e401d3232c084b281f2fff27420002d007232cffe0a33c5b25c083232c044fd003d0032c0326003ebd10638048adf000e8698180b8d848adf07d201800e98fe99ff6a2687d20699fea6a6a184108349e9ca829405d47141baf8280e8410854658056b84008646582a802e78b127d010a65b509e58fe59f80e78b64c0207d80701b28b9e382f970c892e000f18112e001718119026001f1812f82c207f97840d0c0b002801fa40304144c85005cf1613cb3fccccccc9ed5400a6357003d4308e378040f4966fa5208e2906a4208100fabe93f2c18fde81019321a05325bbf2f402fa00d43022544b30f00623ba9302a402de04926c21e2b3e6303250444313c85005cf1613cb3fccccccc9ed5400603502d33f5313bbf2e1925313ba01fa00d43028103459f0068e1201a44343c85005cf1613cb3fccccccc9ed54925f05e2020120120f0201201110002db4f47da89a1f481a67fa9a9a86028be09e008e003e00b0002fb5dafda89a1f481a67fa9a9a860d883a1a61fa61ff4806100043b8b5d31ed44d0fa40d33fd4d4d43010245f04d0d431d430d071c8cb0701cf16ccc98f34ea10e"  # noqa

    def __init__(
        self,
        owner_address: Address,
        next_item_index: int,
        content: CollectionOffchainContent,
        royalty_params: RoyaltyParams,
    ) -> None:
        super().__init__(
            owner_address=owner_address,
            next_item_index=next_item_index,
            content=content,
            royalty_params=royalty_params,
        )

    @classmethod
    def build_mint_body(
        cls,
        index: int,
        owner_address: Address,
        amount: int = 20000000,
        query_id: int = 0,
    ) -> Cell:
        return super().build_mint_body(
            index=index,
            owner_address=owner_address,
            amount=amount,
            query_id=query_id,
        )

    @classmethod
    def build_batch_mint_body(
        cls,
        data: List[Tuple[NFTOffchainContent, Address]],
        from_index: int,
        amount_per_one: int = 20000000,
        query_id: int = 0,
    ) -> Cell:
        return super().build_batch_mint_body(
            data=data,
            from_index=from_index,
            amount_per_one=amount_per_one,
            query_id=query_id,
        )


class CollectionStandardModified(CollectionStandardBase):
    # https://github.com/nessshon/nft-contracts/blob/main/standard/func/nft-collection.func
    CODE_HEX = "b5ee9c724102140100020d000114ff00f4a413f4bcf2c80b0102016202030202cc04050201200e0f04e7d90638048adf000e8698180b8d848adf07d201800e98fe99ff6a2687d20699fea6a6a184108349e9ca829405d47141baf8280e8410854658056b84008646582a802e78b127d010a65b509e58fe59f80e78b64c0207d807029c26382f970c893e000f18113e00171811a136001f1812f8290e002c060708090201480a0b006436363602d33f5313bbf2e1925313ba01fa00d43027103459f00b8e1201a45521c85005cf1613cb3fccccccc9ed54925f05e200a63636367003d4308e378040f4966fa5208e2906a4208100fabe93f2c18fde81019321a05325bbf2f402fa00d43022544a30f00b23ba9302a402de04926c21e2b3e630324434c85005cf1613cb3fccccccc9ed54002e35353501fa40305530c85005cf1613cb3fccccccc9ed5400548e21708018c8cb055004cf1623fa0213cb6acb1fcb3f820afaf08070fb02c98306fb00e05f03840ff2f0002d501c8cb3ff828cf16c97020c8cb0113f400f400cb00c980201200c0d001b3e401d3232c084b281f2fff27420003d16bc025c087c029de0063232c15633c594013e8084f2dac4b333325c7ec0200201201011001fbc82df6a2687d20699fea6a6a182dac40007b8b5d3180201201213002fb5dafda89a1f481a67fa9a9a860d883a1a61fa61ff480610002db4f47da89a1f481a67fa9a9a86028be09e012e003e01500a97eda5"  # noqa

    def __init__(
        self,
        owner_address: Address,
        next_item_index: int,
        content: Union[
            CollectionModifiedOnchainContent, CollectionModifiedOffchainContent
        ],
        royalty_params: RoyaltyParams,
    ) -> None:
        super().__init__(
            owner_address=owner_address,
            next_item_index=next_item_index,
            content=content,
            royalty_params=royalty_params,
        )

    @classmethod
    def build_mint_body(
        cls,
        index: int,
        owner_address: Address,
        amount: int = 20000000,
        query_id: int = 0,
    ) -> Cell:
        return super().build_mint_body(
            index=index,
            owner_address=owner_address,
            amount=amount,
            query_id=query_id,
        )

    @classmethod
    def build_batch_mint_body(
        cls,
        data: List[
            Tuple[Union[NFTModifiedOnchainContent, NFTModifiedOffchainContent], Address]
        ],
        from_index: int,
        amount_per_one: int = 20000000,
        query_id: int = 0,
    ) -> Cell:
        return super().build_batch_mint_body(
            data=data,
            from_index=from_index,
            amount_per_one=amount_per_one,
            query_id=query_id,
        )

    @classmethod
    def build_return_balance(cls, query_id: int = 0) -> Cell:
        """
        Builds the body of the return balance transaction.

        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the return balance transaction.
        """
        return (
            begin_cell()
            .store_uint(RETURN_COLLECTION_BALANCE_OPCODE, 32)
            .store_uint(query_id, 64)
            .end_cell()
        )


class SweetCollectionStandard(CollectionStandardBase):
    # https://github.com/sweet-io-org/miniapp-nft-contracts/blob/master/contracts/nft/standard_nft_collection.fc
    CODE_HEX = "b5ee9c7241021401000255000114ff00f4a413f4bcf2c80b01020162020d0202cc030c020120040904edd10638048adf000e8698180b8d848adf07d201800e98fe99ff6a2687d20699fea6a6a184108349e9ca829405d47141baf8280e8410854658056b84008646582a802e78b127d010a65b509e58fe59f80e78b64c0207d80701b28b9e382f970c8b8a9305d71813929305d718139a9305d7181181aba0a5d405060708006635547000ba20997a5230ba93f2c18fdede04fa00d4302859f008028e1201a44343c85005cf1613cb3fccccccc9ed54925f05e200a6357003d4308e378040f4966fa5208e2906a45304a07aba93f2c18fde81019321a05325bbf2f402fa00d43022544b30f00823ba9302a402de04926c21e2b3e6303250444313c85005cf1613cb3fccccccc9ed540052323401fa40302020d749c10292307095d30130c300e2f2e1954144c85005cf1613cb3fccccccc9ed5400628e28d421d0d749830bbbf2e25bd43020d0d749830cbbf2e25d103458c85005cf1613cb3fccccccc9ed54e05f04840ff2f00201580a0b002d007232cffe0a33c5b25c083232c044fd003d0032c03260001b3e401d3232c084b281f2fff274200051d90686ba4c185ddf9712cad78033810f803bbc00c646582ac678b28027d0109e5b589666664b8fd8040201200e130201200f100043b8b5d31ed44d0fa40d33fd4d4d43010245f04d0d431d430d071c8cb0701cf16ccc980201201112002fb5dafda89a1f481a67fa9a9a860d883a1a61fa61ff480610002db4f47da89a1f481a67fa9a9a86028be09e00ce003e00f00025bc82df6a2687d20699fea6a6a182de86a182c49d2cb760"

    def __init__(
        self,
        owner_address: Address,
        next_item_index: int,
        content: SweetOffchainContent,
        royalty_params: RoyaltyParams,
    ) -> None:
        super().__init__(
            owner_address=owner_address,
            next_item_index=next_item_index,
            content=content,
            royalty_params=royalty_params,
        )

    @classmethod
    def build_mint_body(
        cls,
        owner_address: Address,
        amount: int = get_gas_fee(),
        query_id: int = 0,
        admin_mint: Optional[bool] = False,
    ) -> Cell:
        """
        Builds the body of the mint transaction.

        :param owner_address: The address of the owner.
        :param amount: The amount of coins in nanoton. Defaults to 20000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the mint transaction.
        """
        op_code = ADMIN_NFT_MINT_OPCODE if admin_mint else NFT_MINT_OPCODE
        return (
            begin_cell()
            .store_uint(op_code, 32)
            .store_uint(query_id, 64)
            .store_coins(amount)
            .store_ref(begin_cell().store_address(owner_address).end_cell())
            .end_cell()
        )

    @classmethod
    def build_batch_mint_body(
        cls,
        addresses: List[Address],
        amount_per_one: int = 20000000,
        query_id: int = 0,
    ) -> Cell:

        items_dict = HashMap(key_size=64)

        for i, owner_address in enumerate(addresses, start=0):
            items_dict.set_int_key(
                i,
                begin_cell()
                .store_ref(
                    begin_cell()
                    .store_ref(begin_cell().store_address(owner_address).end_cell())
                    .store_coins(amount_per_one)
                    .end_cell()
                )
                .end_cell(),
            )

        return (
            begin_cell()
            .store_uint(BATCH_NFT_MINT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_dict(items_dict.serialize())
            .end_cell()
        )
