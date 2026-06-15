import pytest

from src.utils.http import HttpClient


def test_mercadolibre_excluded():
    client = HttpClient(
        user_agent="Test",
        delay=0,
        excluded_domains=["mercadolibre.com.ar", "mercadolibre.cl"],
    )
    with pytest.raises(ValueError, match="excluida"):
        client.get("https://www.mercadolibre.com.ar/uniforme-medico")
    with pytest.raises(ValueError, match="excluida"):
        client.get("https://www.mercadolibre.cl/uniforme-medico")
    client.close()
