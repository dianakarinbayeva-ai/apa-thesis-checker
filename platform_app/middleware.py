from django.utils import translation


class InterfaceLanguage:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.session.get("language", "kk")
        request.LANGUAGE_CODE = lang if lang in ("kk", "ru", "en") else "kk"
        with translation.override(request.LANGUAGE_CODE):
            response = self.get_response(request)
        response.headers["Content-Language"] = request.LANGUAGE_CODE
        return response
