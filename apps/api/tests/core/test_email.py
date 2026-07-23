from app.core.email import otp_email, otp_email_html


def test_otp_email_html_contains_code_and_is_html() -> None:
    code = "123456"
    html = otp_email_html(code)
    assert "<html" in html
    # цифры кода присутствуют по порядку (в блоке они разделены пробелами)
    assert " ".join(code) in html
    # текстовая версия остаётся fallback-ом с тем же кодом
    _subject, body = otp_email(code)
    assert code in body
