## integritas_docs.py

docs = '''
API Docs
This documentation provides a detailed overview of the Integritas API, which enables both uploading and verification of data hashes against the blockchain. It supports optional NFT traceability and returns structured results that include on-chain validation details. Use this guide to understand endpoints, request formats, and how to interpret the verification responses.

Base URL
All API requests are made to the following base URL:


https://integritas.minima.global/core
Referenced as: {{BASE_URL}}

Authentication
Authentication is required and done through the use of API-keys. Get yours at https://integritas.minima.global/.

Endpoints
There are five available endpoints.

Three endpoints are used for stamping data. First, preparing data to be stamped by hashing it. Second, stamping data by uploading the hashed data. Third, retrieving proof of stamped data.

One endpoint is used for for verifying data.

Stamping data
Use the first endpoint to send the file. You will receive the SHA3-256 hash of the data in the response.

Use the second endpoint to send the hash. You will receive a UID in the response.

Use the third endpoint to send the UID from the response to retrieve the proof of the time stamping.

Endpoint 1 - Send file and get hash
Attribute	Details
Method	POST
Description	This endpoint is used to submit a file. Send the file as formdata in the body.
Endpoint	{{BASE_URL}}/v1/file/hash
Request Headers

Header	Value	Description
Content-Type	multipart/form-data	Specifies the content type as JSON
x-api-key	your-api-key	Add your API-key from your profile at https://integritas.minima.global/
x-request-id	your-choice	Add a request id to trace every step of the process
Request Body

Request Type	Content-Type	Body Type	Keys	Description
File upload	multipart/form-data	form-data	file	Send file
cURL example:


curl -X POST {{BASE_URL}}/v1/file/hash \
  -H "x-api-key: your-api-key" \
  -H "x-request-id: test-123" \
  -F "file=@path/to/yourfile.docx"
API Response

The response from the API contains the hash of the file.

Example response:


{
    "apiVersion": 1,
    "requestId": "postman-req-id",
    "status": "success",
    "statusCode": 200,
    "message": "Hash computed",
    "timestamp": "2025-06-11T08:12:42.654Z",
    "data": {
        "hash": "C74C4DDE95A49EAFDBA139568E9955C65E017B55662132FA824AF58E6E782427",
        "filename": "test.docx",
        "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
}
Endpoint 2 - Send hash and get UID
Attribute	Details
Method	POST
Description	This endpoint is used to submit hashed data. Send the hash as raw JSON data in the body.
Endpoint	{{BASE_URL}}/v1/timestamp/post
Request Headers

Header	Value	Description
Content-Type	application/json	Specifies the content type as JSON
x-api-key	your-api-key	Add your API-key from your profile at https://integritas.minima.global/
x-request-id	your-choice	Add a request id to trace every step of the process
Request Body

Request Type	Content-Type	Body Type	Keys	Description
Raw data	application/json	JSON	hash	Input hash of data
Example:



{"hash": "C74C4DDE95A49EAFDBA139568E9955C65E017B55662132FA824AF58E6E782427"}
API Response

The response from the API contains a UID which you will need to retrieve proof of the blockchain transaction that is being done by the stamp server:

Example response:


{
    "apiVersion": 1,
    "requestId": "my-test-reqest-id",
    "status": "success",
    "statusCode": 200,
    "message": "Hash forwarded successfully",
    "timestamp": "2025-06-11T08:14:18.227Z",
    "data": {
        "status": true,
        "data": "0xC74C4DDE95A49EAFDBA139568E9955C65E017B55662132FA824AF58E6E782427",
        "uid": "0x4A5AF1550313DAAF728A"
    }
}
Endpoint 3 - Send UID and get proof
Attribute	Details
Method	POST
Description	This endpoint is used to collect the proof from one or multiple blockchain transactions.
Endpoint	{{BASE_URL}}/v1/timestamp/status
Request Headers

Header	Value	Description
Content-Type	application/json	Specifies the content type as JSON
x-api-key	your-api-key	Add your API-key from your profile at https://integritas.minima.global/
x-request-id	your-choice	Add a request id to trace every step of the process
Request Body

Request Type	Content-Type	Body Type	Keys	Description
Raw data	application/json	JSON	uids	Input array of uids.
Example:



{"uids": ["0xFD6C5E119105643FF6DF"]}
API Response

If the blockchain transaction was not yet completed you will get a response that "onchain": false and you need to wait a moment and try again, maximum wait time for a blockchain transaction to be completed is 3 minutes.



{
    "apiVersion": 1,
    "requestId": "my-test-reqest-id",
    "status": "success",
    "statusCode": 200,
    "message": "UID statuses fetched",
    "timestamp": "2025-06-11T08:14:54.183Z",
    "data": [
        {
            "status": true,
            "uid": "0x4A5AF1550313DAAF728A",
            "data": "0xC74C4DDE95A49EAFDBA139568E9955C65E017B55662132FA824AF58E6E782427",
            "number": 124,
            "datecreated": "2025-06-11 08:14:18",
            "onchain": false
        }
    ]
}
The response from the API contains everything needed to verify that the data was sent to the blockchain. These fields are used in the verification process: "data", "root", "proof", "address". Save them in a json file, see example below the response example.

Example response:


{
    "apiVersion": 1,
    "requestId": "my-test-reqest-id",
    "status": "success",
    "statusCode": 200,
    "message": "UID statuses fetched",
    "timestamp": "2025-06-11T08:15:08.584Z",
    "data": [
        {
            "status": true,
            "uid": "0x4A5AF1550313DAAF728A",
            "data": "0xC74C4DDE95A49EAFDBA139568E9955C65E017B55662132FA824AF58E6E782427",
            "number": 124,
            "datecreated": "2025-06-11 08:14:18",
            "onchain": true,
            "datestamped": "2025-06-11 08:15:03",
            "root": "0x894D4D9B47C622BAD8D77A78871B25FA699523D9BE3B0AA70485814A00A90BD6",
            "proof": "0x000100000100",
            "address": "0xFFEEDD"
        }
    ]
}
Fields and format to be saved for verification in a json file:



[
    {
        "address": "0xFFEEDD",
        "data": "0xC74C4DDE95A49EAFDBA139568E9955C65E017B55662132FA824AF58E6E782427",
        "proof": "0x000100000100",
        "root": "0x894D4D9B47C622BAD8D77A78871B25FA699523D9BE3B0AA70485814A00A90BD6"
    }
]
Verification endpoint
Verify data by sending the the source file and the proof file to this endpoint.

NFT Proof Trace (Optional Feature)

The NFT Proof Trace is an optional feature in the API that allows you to request an NFT trace of the verification process.

When enabled:

It provides an immutable, on-chain record of the validation.
The verification is linked to a unique NFT, ensuring transparency and traceability.
Endpoint 4 - Verify data (Using source data)
Attribute	Details
Method	POST
Description	This endpoint is used to submit one or two files for data verification against the blockchain. It processes the provided data and proof (if provided) and returns the verification results.
Endpoint	{{BASE_URL}}/v1/verify/post
Request Headers

Header	Value	Description
Content-Type	application/json	Specifies the content type as JSON
x-api-key	your-api-key	Add your API-key from your profile at https://integritas.minima.global/
x-report-required	"true" / "false"	Request NFT trace from the verification process
x-request-id	your-choice	Add a request id to trace every step of the process
Request Body (Choose one)

Request Type	Content-Type	Body Type	Keys	Description
File upload	file	form-data	file	Validate a source file.
File upload	file	form-data	file	Validate a .tar file. The .tar file should contain the source file and a JSON proof file.
File upload	file + file	form-data	file, jsonproof	Validate a source file with a JSON proof file.
API Response

The response from the API contains information about a file and its results from on-chain verification.

Example response:


{
    "api_version": 1,
    "requestId": "474785f4-4882-41b4-98fd-0d3a5b66001a",
    "response_time": "3172.47 ms",
    "response": {
        "fileHash": "0xC74C4DDE95A49EAFDBA139568E9955C65E017B55662132FA824AF58E6E782427",
        "fileName": "test.docx",
        "fileSize": 279151,
        "result": "full match",
        "method": "timestamp",
        "hash_instances_onchain": 1,
        "unique_hashes": 1,
        "blockchain_data": [
            {
                "block_number": "1520036",
                "block_date": "2025-06-11 08:15:33",
                "txpow_id": "0x0000000FFA25BBEEA02D0F6ABF7F70A54E7C43792C1DBB0C2F766C5497587243",
                "transactionid": "0x3CC2C3B62A4953BEF539F420C879974977BA76222A353DCD5BE6D6246227607A",
                "matched_hash": "0xC74C4DDE95A49EAFDBA139568E9955C65E017B55662132FA824AF58E6E782427"
            }
        ],
        "fileSegments": [
            {
                "matched_hash": "0xC74C4DDE95A49EAFDBA139568E9955C65E017B55662132FA824AF58E6E782427",
                "index": 0,
                "offset": 0,
                "packetSize": 279151
            }
        ]
    }
}
Endpoint 5 - Verify hashed data (Using only proof file)
Attribute	Details
Method	POST
Description	This endpoint is used to submit one proof file for data verification against the blockchain. It processes the proof (if provided) and returns the verification results.
Endpoint	{{BASE_URL}}/v1/verify/post-lite
Request Headers

Header	Value	Description
Content-Type	application/json	Specifies the content type as JSON
x-api-key	your-api-key	Add your API-key from your profile at https://integritas.minima.global/
x-report-required	"true"	Request NFT trace from the verification process is required.
x-request-id	your-choice	Add a request id to trace every step of the process
Request Body (Choose one)

Request Type	Content-Type	Body Type	Keys	Description
File upload	file	form-data	jsonproof	Validate a JSON proof file.
API Response

The response from the API contains information about a file and its results from on-chain verification.

Example response:


{
    "apiVersion": 1,
    "requestId": "test",
    "status": "success",
    "statusCode": 200,
    "message": "Verification complete",
    "timestamp": "2025-07-17T16:55:30.123Z",
    "data": {
        "api_version": 1,
        "requestId": "test",
        "response_time": "29423.18 ms",
        "response": {
            "fileHash": "0x96ED06DE42695E3F807B3E58AB6A2938B43CB037CA11F6DDB4AD5E3DC50D5D4B",
            "nftcoinid": "0x685DFBCF499A0DAF81910B4D1447CF3B992F6B96EB37EE6852445AFA54A8F438",
            "nfttxnid": "0x00000F81BB25316401F76B45DEBAAA706D1840EB6AEC418FD0F33FB3A148BB85",
            "data": {
                "result": "full match",
                "validationMethod": "timestamplite",
                "blockchain_data": [
                    {
                        "block_number": 1541117,
                        "block_date": "2025-06-23 13:32:20",
                        "txpow_id": "0x00000002A52F4DA9370533D0072E32563BEC46A2492AFA5CE6D87E7F6D03B21D",
                        "transactionid": "0x060EE327ED67558CE0849ECFA0B2C35F426F768FEF98726B23715986ABF4FCAD",
                        "matched_hash": "0x96ED06DE42695E3F807B3E58AB6A2938B43CB037CA11F6DDB4AD5E3DC50D5D4B"
                    },
                    {
                        "block_number": 1546070,
                        "block_date": "2025-06-26 10:09:29",
                        "txpow_id": "0x00000028616DDC21E75F9892C748DD64EBD86A257EE044C2563F2D5425808906",
                        "transactionid": "0x8B915CCC208D68962DF4C8EE48151B471C1534F42C37A71110B75BCA920AFC57",
                        "matched_hash": "0x96ED06DE42695E3F807B3E58AB6A2938B43CB037CA11F6DDB4AD5E3DC50D5D4B"
                    }
                ]
            }
        }
    }
}
Below is an explanation of the key fields in the response:

Field	Type	Description
fileHash	string	The unique hash value of the file that was submitted for verification. Used to identify it on-chain.
result	string	The result of the verification process. Possible values: exact match, partial match, or no match.
nftcoinid	string	Unique id of the NFT on the blockchain.
nfttxnid	string	Unique TxPoW id of the transaction that made the NFT.
method	string	The method used to verify the file.
hash_instances_onchain	number	Number of times this file’s hash appears on the blockchain.
unique_hashes	number	Number of unique hashes related to this file found on the blockchain.
blockchain_data	array	Array of found blocks related to the file. See Breakdown of blockchain_data for details.
fileSegments	array	Array of matched segments in the file. See Breakdown of fileSegments for details.
Breakdown of blockchain_data

Field	Type	Description
block_number	string	Block number where the hash was found.
block_date	string	Timestamp in YYYY-MM-DD HH:mm:ss format when the hash was recorded.
txpow_id	string	Transaction ID of the Proof-of-Work where the hash was included.
transactionid	string	Unique ID of the blockchain transaction that contains the matched hash.
matched_hash	string	The matched hash value found in the block.
Breakdown of fileSegments

Field	Type	Description
matched_hash	string	Hash value of a specific segment of the file (chunk).
index	number	Index of the chunk within the file.
offset	number	Offset of the chunk in the file (position in original file).
packetsize	number	Length in bytes of the matching chunk.
'''