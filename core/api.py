import logging
from core.meshok_api import MeshokAPI
from core.templates import LotData
from auto_lot_сonfig import prolong, localDeliveryPrice, countryDeliveryPrice, worldDeliveryPrice

logger = logging.getLogger(__name__)


def make_lot(data: LotData, pic_urls: list[str], account_token: str) -> dict:
    api = MeshokAPI(account_token)
    params = {
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
        "antisniper": "Y" if data.autoprod == "1" else "N",
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
    }
    result = api.listItem(params)
    logger.info("lot posted urls=%s result=%s", pic_urls, result)
    return result
