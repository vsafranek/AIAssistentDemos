from typing import Literal
import os
PROVIDERS = Literal['AKKODIS', 'OPENAI']

AKKODIS_API_KEY: str = os.getenv("AKKODIS_API_KEY", "8630945d228b4bb0ad89ced8652f0616")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
PROVIDER: PROVIDERS = os.getenv("PROVIDER", "AKKODIS")

if AKKODIS_API_KEY == "" and PROVIDER == 'AKKODIS':
    raise Exception("You've selected AKKODIS API for accessing the models without providing your api key.")

if OPENAI_API_KEY == "" and PROVIDER == 'OPENAI':
    raise Exception("You've selected OPENAI API for accessing the models without providing your api key.")

if PROVIDER not in ['AKKODIS', 'OPENAI']:
    raise Exception("You have not selected a valid provider.")
