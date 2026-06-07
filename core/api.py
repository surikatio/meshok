import logging
from core.meshok_api import MeshokAPI
from core.templates import LotData
from core.settings import AppSettings

logger = logging.getLogger(__name__)


def make_lot(data: LotData, pic_urls: list[str], settings: AppSettings, api: MeshokAPI) -> dict:
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
        "prolong": settings.prolong,
        "antisniper": "Y" if data.autoprod == "1" else "N",
        "notify": "Y",
        "tags": ",".join(t.strip() for t in data.tags.split(",") if t.strip()),
        "localDelivery": "CHARGE",
        "localDeliveryPrice": settings.local_delivery_price,
        "countryDeliveryPrice": settings.country_delivery_price,
        "worldDeliveryPrice": settings.world_delivery_price,
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
