import os

# 열린국회정보 API 키 (https://open.assembly.go.kr)
OPEN_ASSEMBLY_API_KEY = os.getenv("OPEN_ASSEMBLY_API_KEY", "145bca1e52594533863a5b12ec70dbc9")

# 국회도서관 API 키 (http://lnp.nanet.go.kr)
NATIONAL_ASSEMBLY_LIBRARY_API_KEY = os.getenv("NATIONAL_ASSEMBLY_LIBRARY_API_KEY", "9f665ae0aeea4ed1bc2f23e1326456a2")
