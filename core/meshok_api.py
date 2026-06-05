import requests


class MeshokAPI:
    def __init__(self, token):
        self.baseUrl = 'https://api.meshok.net/sAPIv1/'
        self.token = token

    def sendRequest(self, method, params={}):
        url = self.baseUrl + method
        headers = {'Authorization': 'Bearer ' + self.token}
        response = requests.post(url, data=params, headers=headers)
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
        return self.sendRequest('listItem', params)

    def updateItem(self, params):
        return self.sendRequest('updateItem', params)
