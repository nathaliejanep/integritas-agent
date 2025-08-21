import json

def final_hash_confirmation(proof: dict) -> str:
    return (
        "🎉 Confirmed on blockchain!\n\n"
        "Your hash has been successfully confirmed on the blockchain. "
        "This proof data can be used for later verification on the blockchain.\n\n"
        "**Proof Data:**\n"
        "```json\n"
        f"{json.dumps(proof, indent=2)}\n"
        "```\n"
    )

def verification_report(verification_result: dict, ai_reasoning: str) -> str:
    try:
        result = verification_result["data"]["response"]["data"]["result"]
    except Exception:
        # fall back to a compact dump
        return f"Verification result:\n```json\n{json.dumps(verification_result, indent=2)}\n```\n\n{ai_reasoning}"

    if result == "full match":
        bd = verification_result["data"]["response"]["data"]["blockchain_data"][0]
        date = bd["block_date"]
        block_number = bd["block_number"]
        txpow_id = bd["txpow_id"]
        txnid = verification_result["data"]["response"]["nfttxnid"]

        # No links per your prompt policy—just show ids
        table = (
            "## Verification Report\n\n"
            "|  |  |\n|---|---|\n"
            f"| **Result** | {result} |\n"
            f"| **Date** | {date} |\n"
            f"| **Block** | {block_number} (txpow {txpow_id}) |\n"
            f"| **NFT Proof** | Verification ID {txnid} |\n"
        )
        return (
            "🎉 Proof Verified!\n\nYour proof has been successfully verified.\n\n"
            f"{table}\n\n"
            "## Intelligent analysis\n\n"
            "(AI can make mistakes. Check important info.)\n\n---\n"
            f"{ai_reasoning}\n---\n"
        )

    return (
        "✅ Verification completed\n\n"
        f"Result: **{result}**\n\n"
        f"{ai_reasoning}\n---\n"
    )
