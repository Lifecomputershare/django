from rest_framework.response import Response


def api_success(data=None, message="", status_code=200):
    body = {
        "success": True,
        "data": data,
        "error": None,
    }
    if message:
        body["message"] = message
    return Response(body, status=status_code)


def api_error(error, status_code):
    return Response(
        {
            "success": False,
            "data": None,
            "error": error,
        },
        status=status_code,
    )

