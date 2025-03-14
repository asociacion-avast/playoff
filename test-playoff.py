from playoff import PlayoffAPI, PlayoffWeb
import json


# p = PlayoffWeb()


# web = PlayoffWeb()

# manolo = api.get_colegiat("23919743L")

# print(json.dumps(manolo))

# print(web.create_inscripcio(idColegiat=3543, idActivitat=714))
# print(web.get_token())

api = PlayoffAPI()
api.del_inscripcio(25409)
api.create_inscripcio(passaport="22as5ASD", idActivitat="714")
