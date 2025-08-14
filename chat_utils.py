## chat_utils.py

import json
from datetime import datetime, timezone
from uuid import uuid4
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from integritas_docs import docs
from config import client

async def ai_reasoning(ctx,sender, reason):
    # Collect all the text chunks
    text = ''
    for item in reason:
        if isinstance(item, TextContent):
            text += item.text

    try:
      # Query ASI:One to understand if this is a hash stamping request or a general question
        r = client.chat.completions.create(
            model="asi1-mini",
            messages=[
                {"role": "system", "content": f"""
                    You are an expert assistant specializing in analyzing blockchain data and verification results.
                    You will receive information indicating whether specific data has been published on the blockchain,
                    along with metadata such as the hash, proof, root, and timestamp.
                 
                    This is documentation from the API, explain the result based on the docs: {docs}

                    Your task is to summarize the verification result in clear, natural language,
                    and highlight the **date when the data was hashed** on the blockchain (if available).
                    
                    If the data has not yet been published on-chain, explain this clearly.
                    Do not include any links in your responses.
                    Keep your tone polite, professional, and informative.
                """},
                {"role": "assistant", "content": f"Please explain: {reason}. Make it comprehensive, practical, and easy to understand. Skip the introductions and get right into the explanation. Limit the answer to 3-4 topics, use icons and headings to make it easily digestible."},
            ],
            max_tokens=2048,
        )

        response = str(r.choices[0].message.content)
        ctx.logger.info(f"{response}")
        return response

    except Exception as e:
        ctx.logger.exception('Error querying ASI:One model')
        response = 'I am afraid something went wrong and I am unable to process your request at the moment'

            # Send the response back to the user (only if we haven't already sent responses)
    if response is not None:
        await ctx.send(sender, ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[
                # Send the contents back in the chat message
                TextContent(type="text", text=response),
                # Signal that the session is over
                EndSessionContent(type="end-session"),
            ]
        ))

def format_response(verification_result, ai_reason_response):

    result = verification_result['data']['response']['data']['result']

    if result == 'full match':
        date = verification_result['data']['response']['data']['blockchain_data'][0]['block_date']
        block_number = verification_result['data']['response']['data']['blockchain_data'][0]['block_number']
        txpow_id = verification_result['data']['response']['data']['blockchain_data'][0]['txpow_id']
        txnid = verification_result['data']['response']['nfttxnid']
        explorerlink = f'https://explorer.minima.global/transactions/{txnid}'
        block_link = f'https://explorer.minima.global/blocks/{txpow_id}'

        final_response = (
            f"🎉 Proof Verified!\n\n"
            f"Your proof has been successfully verified.\n\n"

            "## Verification Report\n\n"
            "|  |  |\n"
            "|---|---|\n"
            f"| **Result**     | {result} |\n"
            f"| **Date**       | {date} |\n"
            f"| **Block**      | [{block_number}]({block_link}) |\n"
            f"| **NFT Proof**  | [Verification ID]({explorerlink}) |\n"
       
            "\n\n\n"

            f"## Intelligent report analyzation\n\n"
            f"(AI can make mistakes. Check important info.).\n\n---\n"
            f"{ai_reason_response}\n\n---\n"
            f"Visit [Integritas](https://integritas.minima.global/) to take your data integrity to the next level."
        )
    else:
        final_response = (
            f"🎉 Proof Verified!\n\n"
            f"Your proof has been successfully verified.\n\n"
            f"Result: {result}\n\n"
            f"{ai_reason_response}\n\n---\n"
            f"Visit [Integritas](https://integritas.minima.global/) to take your data integrity to the next level."
        )
    
    return final_response


def format_final_hash_response(proof_data):
    # Format the JSON for display
    json_content = json.dumps(proof_data, indent=2)

    final_response = f'''🎉 Confirmed on blockchain!

Your hash has been successfully confirmed on the blockchain. This proof data can be used for later verification on the blockchain.

**Proof Data:**
```json
{json_content}
```
'''
    
    return final_response