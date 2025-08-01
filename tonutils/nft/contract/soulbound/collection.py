from __future__ import annotations

from typing import List, Tuple, Optional, Union

from pytoniq_core import Address, Cell, begin_cell, HashMap

from .nft import NFTSoulbound
from ..base.collection import Collection, get_gas_fee
from ...content import (
    CollectionOffchainContent,
    CollectionModifiedOnchainContent,
    CollectionModifiedOffchainContent,
    NFTOffchainContent,
    NFTModifiedOnchainContent,
    NFTModifiedOffchainContent,
    SweetOffchainContent,
)
from ...data import CollectionData
from ...op_codes import *
from ...royalty_params import RoyaltyParams


class CollectionSoulboundBase(Collection):

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
        self._data = self.create_data(owner_address, next_item_index, content, royalty_params).serialize()
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
            nft_item_code=NFTSoulbound.CODE_HEX,
        )

    @classmethod
    def build_mint_body(
            cls,
            index: int,
            owner_address: Address,
            content: Union[
                NFTOffchainContent,
                NFTModifiedOnchainContent,
                NFTModifiedOffchainContent,
            ],
            authority_address: Optional[Address] = None,
            revoked_at: int = 0,
            amount: int = 20000000,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the mint transaction.

        :param index: The index of the nft to be minted.
        :param content: The content of the nft to be minted.
        :param owner_address: The address of the owner.
        :param authority_address: The address of the authority. Defaults to the owner address.
        :param revoked_at: The timestamp when the nft is revoked. Defaults to 0.
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
            .store_ref(
                begin_cell()
                .store_address(owner_address)
                .store_ref(content.serialize())
                .store_address(authority_address or owner_address)
                .store_uint(revoked_at, 64)
                .end_cell()
            )
            .end_cell()
        )

    @classmethod
    def build_batch_mint_body(
            cls,
            data: List[Tuple[Union[
                NFTOffchainContent,
                NFTModifiedOnchainContent,
                NFTModifiedOffchainContent,
            ], Address, Optional[Address], Optional[int]]],
            from_index: int,
            amount_per_one: int = 20000000,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the batch mint transaction.

        :param data: The list of data for minting. Each tuple contains:
            - OffchainCommonContent: The content of the nft to be minted.
            - Address: The address of the owner.
            - Optional[Address]: The address of the authority (if any) defaults to the owner address.
            - int: The timestamp when the nft is revoked. DDefaults to 0.
        :param from_index: The starting index for minting.
        :param amount_per_one: The amount of coins in nanoton per nft. Defaults to 20000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the batch mint transaction.
        """
        items_dict = HashMap(key_size=64)

        for i, (content, owner_address, authority_address, revoked_at) in enumerate(data, start=0):
            items_dict.set_int_key(
                i + from_index,
                begin_cell()
                .store_coins(amount_per_one)
                .store_ref(
                    begin_cell()
                    .store_address(owner_address)
                    .store_address(authority_address or owner_address)
                    .store_uint(revoked_at or 0, 64)
                    .store_ref(content.serialize())
                    .end_cell()
                )
                .end_cell()
            )

        return (
            begin_cell()
            .store_uint(BATCH_NFT_MINT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_dict(items_dict.serialize())
            .end_cell()
        )


class CollectionSoulbound(CollectionSoulboundBase):
    CODE_HEX = "b5ee9c724102140100021f000114ff00f4a413f4bcf2c80b0102016202030202cd04050201200e0f04e7d10638048adf000e8698180b8d848adf07d201800e98fe99ff6a2687d20699fea6a6a184108349e9ca829405d47141baf8280e8410854658056b84008646582a802e78b127d010a65b509e58fe59f80e78b64c0207d80701b28b9e382f970c892e000f18112e001718112e001f181181981e0024060708090201200a0b00603502d33f5313bbf2e1925313ba01fa00d43028103459f0068e1201a44343c85005cf1613cb3fccccccc9ed54925f05e200a6357003d4308e378040f4966fa5208e2906a4208100fabe93f2c18fde81019321a05325bbf2f402fa00d43022544b30f00623ba9302a402de04926c21e2b3e6303250444313c85005cf1613cb3fccccccc9ed54002c323401fa40304144c85005cf1613cb3fccccccc9ed54003c8e15d4d43010344130c85005cf1613cb3fccccccc9ed54e05f04840ff2f00201200c0d003d45af0047021f005778018c8cb0558cf165004fa0213cb6b12ccccc971fb008002d007232cffe0a33c5b25c083232c044fd003d0032c03260001b3e401d3232c084b281f2fff2742002012010110025bc82df6a2687d20699fea6a6a182de86a182c40043b8b5d31ed44d0fa40d33fd4d4d43010245f04d0d431d430d071c8cb0701cf16ccc980201201213002fb5dafda89a1f481a67fa9a9a860d883a1a61fa61ff480610002db4f47da89a1f481a67fa9a9a86028be09e008e003e00b01a500c6e"  # noqa

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
            content: NFTOffchainContent,
            authority_address: Optional[Address] = None,
            revoked_at: int = 0,
            amount: int = 20000000,
            query_id: int = 0,
    ) -> Cell:
        return super().build_mint_body(
            index=index,
            owner_address=owner_address,
            content=content,
            authority_address=authority_address,
            revoked_at=revoked_at,
            amount=amount,
            query_id=query_id,
        )

    @classmethod
    def build_batch_mint_body(
            cls,
            data: List[Tuple[NFTOffchainContent,
            Address, Optional[Address], Optional[int]]],
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


class CollectionSoulboundModified(CollectionSoulboundBase):
    # https://github.com/nessshon/nft-contracts/blob/main/soulbound/func/nft-collection.func
    CODE_HEX = "b5ee9c72410216010002f8000114ff00f4a413f4bcf2c80b0102016202030202cc04050201200e0f02f7d90638048adf000e8698180b8d848adf07d201800e98fe99ff6a2687d20699fa9906380e0004a187d2000ef00ea6a6a182a814108349e9ca829485d47148b2f83360968410854658056b84008646582a802e78b127d010a65b509e58fe59f80e78b64c0207d807029cae382a9d0e382d8f970c8946000f181146001406070201480a0b007037373703d33f5312bbf2e1925312ba01fa00d43029103459f00b8e18a45044451503c85006cf1614cb3f12cccccc01cf16c9ed54925f06e202fc8e753737377004d45350c701c0009430d201309131e28e45018040f4966fa524c0ff25c001b193315250de208e2908a4208100fabe93f2c18fde81019321a05327bbf2f402fa00d43022544d30f00b25ba9304a404de06926c21e2b312e65b335044451503c85006cf1614cb3f12cccccc01cf16c9ed54e028c003e302280809005030363606810fa103c70512f2f401fa40305423055033c85006cf1614cb3f12cccccc01cf16c9ed5400eec0048e20313235353501d4d4301025440302c85006cf1614cb3f12cccccc01cf16c9ed54e03027c0058e235f06708018c8cb055004cf1623fa0213cb6acb1fcb3f820afaf08070fb02c98306fb00e0363705c0068e1a02fa403045501413c85006cf1614cb3f12cccccc01cf16c9ed54e05f06840ff2f0002d501c8cb3ff828cf16c97020c8cb0113f400f400cb00c980201200c0d001b3e401d3232c084b281f2fff27420003d16bc025c087c029de0063232c15633c594013e8084f2dac4b333325c7ec0200201201011003fbc82df6a2687d20699fa9906380e0004a187d2000ef00ea6a6a182a812f81ac40007b8b5d31802012012130201661415004db4f47da89a1f481a67ea6418e0380012861f48003bc03a9a9a860aa04204abe0be012e003e0150003caa15ed44d0fa40d33f5320c701c0009430fa4001de01d4d4d43055026c51004eaad7ed44d0fa40d33f5320c701c0009430fa4001de01d4d4d4305502155f05d0d30fd30ffa403001d8a761"  # noqa

    def __init__(
            self,
            owner_address: Address,
            next_item_index: int,
            content: Union[CollectionModifiedOnchainContent, CollectionModifiedOffchainContent],
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
            content: Union[NFTModifiedOnchainContent, NFTModifiedOffchainContent],
            authority_address: Optional[Address] = None,
            revoked_at: int = 0,
            amount: int = 20000000,
            query_id: int = 0,
    ) -> Cell:
        return super().build_mint_body(
            index=index,
            owner_address=owner_address,
            content=content,
            authority_address=authority_address,
            revoked_at=revoked_at,
            amount=amount,
            query_id=query_id,
        )

    @classmethod
    def build_batch_mint_body(
            cls,
            data: List[Tuple[Union[NFTModifiedOnchainContent, NFTModifiedOffchainContent],
            Address, Optional[Address], Optional[int]]],
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


class SweetCollectionSoulbound(CollectionSoulboundBase):
    # https://github.com/sweet-io-org/miniapp-nft-contracts/blob/master/contracts/nft/soulbound_nft_collection.fc

    CODE_HEX = "b5ee9c72410211010001cd000114ff00f4a413f4bcf2c80b01020162020c0202cc030b020120040803f5d10638048adf000e8698180b8d848adf07d201800e98fe99f98f6a2687d20699fea6a1828b1e382f970c8b8a9285d471e1a2a38005d104cbd29185d49f960c7ef6f026a10e86ba4c185ddf970cb7d00181381780401470880d22001e42802678b09659fe66664f6aa492f8271703929285d71813a0add71812f82c05060700b4347003d4308e418040f4966fa5208e3306a45304a07aba93f2c18fde81019321a05325bbf2f402d421d0d749830bbbf2e196fa003022544a03f00823ba9302a402de04926c21e2b3e630325023c85004cf1612cb3fccccc9ed54004e03d0d431d4d102d43020d0d749830bbbf2e196c8cc12ccc95003c85004cf1612cb3fccccc9ed540008840ff2f0020158090a002d007232cffe0a33c5b25c083232c044fd003d0032c03260001b3e401d3232c084b281f2fff27420003ddad78033810f803bbc00c646582ac678b28027d0109e5b589666664b8fd8040201200d100201200e0f003fb8b5d31ed44d0fa40d33fd4d430135f03d0d431d430d071c8cb0701cf16ccc980029ba7a3ed44d0fa40d33fd4d4306c31f0067001f00780023bc82df6a2687d20699fea6a1818686a182c496828576"

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
            content: SweetOffchainContent,
            amount: int = get_gas_fee(),
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the mint transaction.

        :param content: The content of the nft to be minted.
        :param owner_address: The address of the owner.
        :param amount: The amount of coins in nanoton. Defaults to 20000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the mint transaction.
        """
        return (
            begin_cell()
            .store_uint(NFT_MINT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_coins(amount)
            .store_ref(
                begin_cell()
                .store_address(owner_address)
                .store_ref(content.serialize())
                .end_cell()
            )
            .end_cell()
        )

    @classmethod
    def build_batch_mint_body(
            cls,
            data: List[Tuple[Union[
                NFTOffchainContent,
                NFTModifiedOnchainContent,
                NFTModifiedOffchainContent,
            ], Address, Optional[Address], Optional[int]]],
            from_index: int,
            amount_per_one: int = get_gas_fee(),
            query_id: int = 0,
    ) -> Cell:
        # We are not supporting batch minting for SweetCollectionSoulbound for the moment.
        raise NotImplementedError