def default_function(payload):
    print(payload)
    return {
        'statusCode': 200,
        'body': "Function just returns after loading dependencies"
    }