import os

import openai
from typing import Tuple, Literal

PROVIDERS = Literal['AZURE', 'OPENAI']

API_BASE: str = os.getenv("API_BASE", "")
API_VERSION: str = os.getenv("API_VERSION", "")
AZURE_API_KEY: str = os.getenv("AZURE_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
PROVIDER = "OPENAI"


def client_gpt_4o() -> Tuple[openai.AzureOpenAI, str]:
    if PROVIDER == 'OPENAI':
        deployment = "gpt-4o"
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

    elif PROVIDER == 'AZURE':
        deployment = "models-gpt-4o"
        client = openai.AzureOpenAI(base_url=API_BASE,
                                    api_key=AZURE_API_KEY,
                                    api_version=API_VERSION)
    return client, deployment


def client_ada_002() -> Tuple[openai.AzureOpenAI, str]:
    if PROVIDER == 'OPENAI':
        deployment = "text-embedding-ada-002"
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

    elif PROVIDER == 'AZURE':
        deployment = "models-ada-002"
        client = openai.AzureOpenAI(base_url=API_BASE,
                                    api_key=AZURE_API_KEY,
                                    api_version=API_VERSION)

    return client, deployment


def get_api_key():
    return OPENAI_API_KEY
