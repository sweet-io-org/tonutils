from typing import Dict, List, Optional


# https://docs.ton.org/v3/documentation/tvm/tvm-exit-codes
class ExitCode:
    _code_map = {
        0: "standard_successful_execution",
        1: "alternative_successful_execution_reserved",
        2: "stack_underflow",
        3: "stack_overflow",
        4: "integer_overflow",
        5: "range_check_error",
        6: "invalid_tvm_opcode",
        7: "type_check_error",
        8: "cell_overflow",
        9: "cell_underflow",
        10: "dictionary_error",
        11: "unknown_error",
        12: "fatal_error",
        13: "out_of_gas",
        -14: "out_of_gas",
        14: "vm_virtualization_error",
        32: "action_list_invalid",
        33: "action_list_too_long",
        34: "action_invalid_or_not_supported",
        35: "invalid_source_address",
        36: "invalid_destination_address",
        37: "not_enough_toncoin",
        38: "not_enough_extra_currencies",
        39: "outbound_message_does_not_fit",
        40: "cannot_process_message",
        41: "library_reference_null",
        42: "library_change_error",
        43: "exceeded_max_cells_or_depth",
        50: "account_state_size_exceeded",
        128: "null_reference_exception",
        129: "invalid_serialization_prefix",
        130: "invalid_incoming_message",
        131: "constraints_error",
        132: "access_denied",
        133: "contract_stopped",
        134: "invalid_argument",
        135: "contract_code_not_found",
        136: "invalid_standard_address",
        137: "masterchain_support_not_enabled",
        138: "not_a_basechain_address",
    }

    @classmethod
    def translate(cls, code: int) -> str:
        if code is None:
            return None
        return cls._code_map.get(code, f"unknown_exit_code_{code}")


class PhaseResult:
    def __init__(
        self,
        success: bool,
        skipped: bool,
        skip_reason: Optional[str],
        exit_code: Optional[int],
    ):
        self.success = success
        self.skipped = skipped
        self.skip_reason = skip_reason
        self.exit_code = exit_code

    @property
    def error(self) -> Optional[str]:
        if self.skipped and self.skip_reason:
            return self.skip_reason.lower().replace(" ", "_")
        if not self.success and self.exit_code is not None:
            return ExitCode.translate(self.exit_code)
        return None


class Transaction:
    def __init__(
        self,
        hash: str,
        block: str,
        account: str,
        success: bool,
        timestamp: int,
        total_fees: int,
        end_balance: int,
        op_code: str,
        compute_phase: PhaseResult,
        action_phase: PhaseResult,
        error: Optional[str] = None,
        interfaces: Optional[
            List[str]
        ] = None,  # contract intrerface, e.g. wallet_v5r1, nft_collection, nft_item
        children: Optional[List["Transaction"]] = None,
    ):
        self.hash = hash
        self.block = str(block)
        self.account = account
        # success here means not failed or aborted (will be set below)
        self.success = success
        self.timestamp = timestamp
        self.total_fees = total_fees
        self.end_balance = end_balance
        self.op_code = op_code
        self.compute_phase = compute_phase
        self.action_phase = action_phase
        self.error = error
        self.interfaces = interfaces or []
        self.children = children or []

    @classmethod
    def from_ton_api_trace(cls, data: Dict) -> "Transaction":
        tx_data = data.get("transaction") if "transaction" in data else data

        def parse_phase(phase: Optional[Dict]) -> PhaseResult:
            if not phase:
                return PhaseResult(
                    success=False,
                    skipped=True,
                    skip_reason="missing_phase_info",
                    exit_code=None,
                )
            if phase.get("skipped", False):
                return PhaseResult(
                    success=False,
                    skipped=True,
                    skip_reason=phase.get("skip_reason", "skipped"),
                    exit_code=None,
                )
            if "exit_code" in phase:
                exit_code = phase.get("exit_code")
            else:
                exit_code = phase.get("result_code")
            return PhaseResult(
                success=phase.get("success", False),
                skipped=False,
                skip_reason=None,
                exit_code=exit_code,
            )

        # Initial success or aborted check
        raw_success = tx_data.get("success", False)
        raw_aborted = tx_data.get("aborted", False)  # assuming aborted field may exist

        # Per your logic, if success is False or aborted True => treat as failed
        success = raw_success and not raw_aborted

        compute_phase = parse_phase(tx_data.get("compute_phase"))
        action_phase = parse_phase(tx_data.get("action_phase"))

        error = None
        # Step 1: check compute_phase skipped
        if compute_phase.skipped:
            error = (
                compute_phase.skip_reason.lower().replace(" ", "_")
                if compute_phase.skip_reason
                else "compute_phase_skipped"
            )
        else:
            # compute_phase ran: check success and exit_code
            if not compute_phase.success:
                error = ExitCode.translate(compute_phase.exit_code)
            else:
                # compute_phase succeeded: check action_phase success and exit_code
                if not action_phase.success:
                    error = ExitCode.translate(action_phase.exit_code)

        # If error present, treat transaction as failed regardless of raw success
        if error is not None:
            success = False

        children = []
        # Only traverse children if this transaction is successful, otherwise traverse seems unnecessary
        if success and data.get("children"):
            for child_data in data["children"]:
                child_tx = cls.from_ton_api_trace(child_data)
                children.append(child_tx)
        interfaces = data.get("interfaces", [])
        if not interfaces and error == "cskip_no_state":
            interfaces = ["uninit"]

        return cls(
            hash=tx_data.get("hash", ""),
            block=tx_data.get("block", ""),
            account=tx_data["account"].get("address"),
            success=success,
            timestamp=tx_data.get("utime", 0),
            total_fees=tx_data.get("total_fees", 0),
            end_balance=tx_data.get("end_balance", 0),
            op_code=tx_data.get("in_msg", {}).get("op_code", 0),
            compute_phase=compute_phase,
            action_phase=action_phase,
            error=error,
            interfaces=interfaces,
            children=children,
        )


class TransactionReceipt:
    def __init__(
        self,
        hash: str,  # hash of the tree root
        block: str,  # block of the tree root
        block_hash: str,
        success: bool,
        batch_transaction: bool,
        raw_transaction: Transaction,
        error: Optional[List[str]] = None,
        interfaces: Optional[
            List[str]
        ] = None,  # contract interfaces, e.g. wallet_v5r1, nft_collection, nft_item
    ):
        self.hash = hash
        self.block = block
        self.block_hash = block_hash
        self.success = success
        self.batch_transaction = batch_transaction
        self.raw_transaction = raw_transaction
        self.error = error or []
        self.interfaces = interfaces

    @classmethod
    def from_transaction(cls, tx: Transaction, block_hash: str) -> "TransactionReceipt":
        def traverse(tx: Transaction):
            collected_errors = []
            batch_node = False
            interfaces = set()

            if tx.interfaces:
                interfaces |= set(tx.interfaces)

            if not tx.success and tx.error:
                collected_errors.append(tx.error)
                return collected_errors, batch_node, interfaces  # stop on failed node

            if len(tx.children) >= 2:
                batch_node = True

            for child in tx.children:
                child_errors, child_batch, child_interfaces = traverse(child)
                collected_errors.extend(child_errors)
                batch_node = batch_node or child_batch
                interfaces |= set(child_interfaces)

            return collected_errors, batch_node, interfaces

        errors, is_batch, interfaces = traverse(tx)

        return cls(
            hash=tx.hash,
            block=tx.block,
            block_hash=block_hash,
            success=len(errors) == 0,
            batch_transaction=is_batch,
            raw_transaction=tx,
            error=errors or None,
            interfaces=list(interfaces) if interfaces else None,
        )
