def success(message, data=None, code=200):

    if data is None:
        data = []

    return {
        "status": "success",
        "message": message,
        "status_code": code,
        "data": data
    }


def failed(message, code=400):

    return {
        "status": "failed",
        "message": message,
        "status_code": code,
        "data": []
    }