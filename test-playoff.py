from playoff import Playoff
import json


idColegiat = "3543"  # manolo el del bombo
idActivitat = "714"  # Gamusino's revenge

# p = PlayoffWeb()


# web = PlayoffWeb()
# res = web.get_colegiat_by_id("3543")
# print(res)

# manolo = api.get_colegiat("23919743L")

# print(json.dumps(manolo))

# print(web.create_inscripcio(idColegiat=3543, idActivitat=714))
# print(web.get_token())

p = Playoff()
# res = api.create_inscripcio(passaport="22as5ASD", idActivitat="714")
p.api.del_inscripcio("25413")
print(p.api.create_inscripcio(idActivitat=idActivitat, idColegiat=idColegiat))
p.api.get_colegiat_by_id()
