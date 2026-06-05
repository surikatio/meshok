import logging
import requests
from core.templates import LotData

# Импорт с кириллической 'с' в имени файла — это намеренно, файл конфига так называется
from auto_lot_сonfig import prolong, localDeliveryPrice, countryDeliveryPrice, worldDeliveryPrice

logger = logging.getLogger(__name__)

API_URL = "https://api.meshok.net/sAPIv1/"


def make_lot(data: LotData, pic_urls: list[str], account_token: str) -> dict:
    autoprod = "Y" if data.autoprod == "1" else "N"
    response = requests.post(
        API_URL + "listItem",
        headers={"Authorization": f"Bearer {account_token}"},
        params={
            "city": "58",
            "name": data.name,
            "curencyId": "2",
            "saleType": "Auction",
            "category": data.category.replace(" ", ""),
            "startPrice": data.price.replace(" ", ""),
            "payment": "BANK,CARD,PAYPAL",
            "longevity": data.longevity,
            "delivery": "WORLD",
            "prolong": prolong,
            "antisniper": autoprod,
            "notify": "Y",
            "tags": data.tags.replace(" ", ""),
            "localDelivery": "CHARGE",
            "localDeliveryPrice": localDeliveryPrice,
            "countryDeliveryPrice": countryDeliveryPrice,
            "worldDeliveryPrice": worldDeliveryPrice,
            "minimalBuyerRate": "0",
            "condition": "NA",
            "listDateTime": data.date,
            "description": data.description,
            "bold": "N",
            "recommended": "N",
            "pictures": ",".join(pic_urls),
            "bestOffer": "Y",
        },
    )
    result = response.json()
    logger.info("lot posted urls=%s result=%s", pic_urls, result)
    return result
