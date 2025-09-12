import json
def shorten_string(s: str, start_chars=6, end_chars=4) -> str:
    """
    Shorten a string by keeping the first `start_chars` and last `end_chars` characters.

    Args:
        s (str): The string to shorten.
        start_chars (int): Number of characters to keep at the start.
        end_chars (int): Number of characters to keep at the end.

    Returns:
        str: Shortened string with ellipsis in the middle.
    """
    if len(s) <= start_chars + end_chars:
        return s  # no need to shorten
    return f"{s[:start_chars]}…{s[-end_chars:]}"
    
def final_hash_confirmation(result: dict) -> str:
    """
    Generate a confirmation message that includes both proof data and download link information.
    
    Args:
        result: The full result from stamping_service.stamp_hash()
    """
    # Extract proof data
    proof = result.get("proof", {})
    
    # Start with the basic confirmation
    message = (
        "🎉 Confirmed on blockchain!\n\n"
        "Your hash has been successfully confirmed on the blockchain. "
        "This proof data can be used for later verification on the blockchain.\n\n"
        "**Proof Data:**\n"
        "```json\n"
        f"{json.dumps(proof, indent=2)}\n"
        "```\n"
    )
    
    # Add download link information if available
    download_link = result.get("downloadLink")
    
    if download_link:
        message += (
            "\n **Proof File Available for Download**\n\n"
            f"**Download Link:**  [Proof File ↓]({download_link})\n\n"
            "💡 **Note:** \n\n"
            "• This download link is valid for 1 hour and can be shared with others.\n\n"
            "• Click on the link, right click and save as to download the file.\n"
        )

    return message

def verification_report(verification_result: dict, ai_reasoning: str) -> str:
    try:
        result = verification_result["data"]["verification"]["data"]["result"]
    except Exception:
        # fall back to a compact dump
        return f"Verification result:\n```json\n{json.dumps(verification_result, indent=2)}\n```\n\n{ai_reasoning}"

    if result == "full match":
        date = verification_result["timestamp"]
        # block_number = bd["block_number"]
        # txpow_id = bd["txpow_id"]
        # transaction_id = bd["transactionid"]
        # txnid = verification_result["data"]["verification"]["data"]["nfttxnid"]
        download_link = verification_result["data"]["file"]["download_url"]

        # No links per your prompt policy—just show ids
        table = (
            "## Verification Report\n\n"
            "|  |  |\n|---|---|\n"
            f"| **Result** | {result} |\n"
            f"| **Verification Date** | {date} UTC |\n"
            # f"| **Blocks** | [{block_number}  ↗](https://explorer.minima.global/blocks/{txpow_id})|\n"
            # f"| **Txn ID** | [{shorten_string(transaction_id)}  ↗](https://explorer.minima.global/transactions/{transaction_id}) |\n"
            # f"| **NFT Proof** | [{shorten_string(txnid)}  ↗](https://explorer.minima.global/transactions/{txnid}) |\n"
        )
        return (
            "🎉 Proof Verified!\n\nYour proof has been successfully verified.\n\n"
            f"{table}\n\n"
            f"### Full Verification Report \n\n"
            f"**Download Link:**  [Report File ↓]({download_link})\n\n"
            "💡 **Note:** \n\n"
            "• This download link is valid for 1 hour and can be shared with others.\n\n---\n"
            
            "## Intelligent analysis\n\n"
            "(AI can make mistakes. Check important info.)\n\n---\n"
            f"{ai_reasoning}\n\n---\n"
            "Visit [Integritas ↗](https://integritas.minima.global) for more information."
        )

    return (
        "✅ Verification completed\n\n"
        f"Result: **{result}**\n\n"
        f"{ai_reasoning}\n\n---\n"
        "Visit [Integritas ↗](https://integritas.minima.global) for more information."
    )
