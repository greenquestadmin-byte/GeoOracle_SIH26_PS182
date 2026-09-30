class TransactionAnalyzer:

    def analyze(self, tx: dict) -> dict:
        inputs = tx.get("inputs", [])
        outputs = tx.get("outputs", [])
        status = tx.get("status", {})

        input_value = sum(
            item.get("value", 0) or 0
            for item in inputs
        )

        output_value = sum(
            item.get("value", 0) or 0
            for item in outputs
        )

        fee = max(
            input_value - output_value,
            0
        )

        input_addresses = [
            item.get("address")
            for item in inputs
            if item.get("address")
        ]

        output_addresses = [
            item.get("address")
            for item in outputs
            if item.get("address")
        ]

        return {
            "tx_hash": tx.get("tx_hash"),
            "network": tx.get("network", "bitcoin"),

            "confirmed": status.get("confirmed"),
            "block_height": status.get("block_height"),
            "block_hash": status.get("block_hash"),
            "block_time": status.get("block_time"),

            "input_count": len(inputs),
            "output_count": len(outputs),

            "input_value": input_value,
            "output_value": output_value,
            "fee": fee,

            "input_addresses": input_addresses,
            "output_addresses": output_addresses,

            "unique_input_addresses": len(
                set(input_addresses)
            ),
            "unique_output_addresses": len(
                set(output_addresses)
            ),
        }