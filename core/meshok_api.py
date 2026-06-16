"""Тонкий клиент REST API meshok.net (sAPIv1), на основе meshokteam/sAPI-py."""

import requests


class MeshokAPI:
    """Сессия с авторизацией Bearer-токеном для одного аккаунта meshok.net."""

    def __init__(self, token):
        self.baseUrl = 'https://api.meshok.net/sAPIv1/'
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'Bearer ' + self.token})

    def sendRequest(self, method, params={}):
        """POST на {baseUrl}{method} с переданными params, возвращает разобранный JSON-ответ."""
        url = self.baseUrl + method
        response = self.session.post(url, data=params, timeout=60)
        return response.json()

    def getItemList(self):
        return self.sendRequest('getItemList')

    def getFinishedItemList(self):
        return self.sendRequest('getFinishedItemList')

    def getUnsoldFinishedItemList(self):
        return self.sendRequest('getUnsoldFinishedItemList')

    def getSoldFinishedItemList(self):
        return self.sendRequest('getSoldFinishedItemList')

    def getItemInfo(self, id):
        return self.sendRequest('getItemInfo', {'id': id})

    def getAccountInfo(self):
        return self.sendRequest('getAccountInfo')

    def getCommonDescriptionList(self):
        return self.sendRequest('getCommonDescriptionList')

    def getSubCategory(self, id):
        return self.sendRequest('getSubCategory', {'id': id})

    def getCategoryInfo(self, id):
        return self.sendRequest('getCategoryInfo', {'id': id})

    def getCurencyList(self):
        return self.sendRequest('getCurencyList')

    def getCountryList(self):
        return self.sendRequest('getCountryList')

    def getCitiesList(self, id):
        return self.sendRequest('getCitiesList', {'id': id})

    def stopSale(self, id):
        return self.sendRequest('stopSale', {'id': id})

    def relistItem(self, id):
        return self.sendRequest('relistItem', {'id': id})

    def deleteItem(self, id):
        return self.sendRequest('deleteItem', {'id': id})

    def listItem(self, params):
        """Публикует новый лот. Используется в core.api.make_lot."""
        return self.sendRequest('listItem', params)

    def updateItem(self, params):
        return self.sendRequest('updateItem', params)
