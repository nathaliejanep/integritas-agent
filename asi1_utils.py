def format_response(verification_result):

    result = verification_result['data']['response']['data']['result']

    
    final_response = f'''
    🎉 **Proof Verified!**
    
    Your proof has been successfully verified. 
    Your verification result: {result}

    '''

    return final_response