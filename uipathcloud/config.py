from pydantic import BaseModel, SecretStr, Field, validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Dict, List, Optional, Type
from uuid import UUID
from .common import SecureDumpModel
from .models.uipathcloud import UiPathCloudOauth2, Organization, Application, AccessToken


from functools import lru_cache

@lru_cache
def get_settings():
    return Settings()

print("############")
print("############")

#SecureDumpModel extends BaseModel to enhance data security by masking sensitive fields for logging.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=('.uipathcloud.env'), #, '.env.prod'),
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        extra='allow',
    )

    app_name: str = "Gata Haystack"
    summary: str = "Automating the UiPath Automation Cloud — Community Edition"
    uipathcloud_baseurl: str = "https://cloud.uipath.com"
    uipathcloud_authorization_endpoint: str = "https://cloud.uipath.com/identity_/connect/authorize"
    uipathcloud_token_endpoint: str = "https://cloud.uipath.com/identity_/connect/token"
    uipathcloud_organizations: List[Organization] = []

    def mask_sensitive_data(self, mask: str = "******") -> Dict[str, Any]:
        data = super().dict()
        if 'uipathcloud_organizations' in data and data['uipathcloud_organizations']:
            for org in data['uipathcloud_organizations']:
                for app in org.get('applications', []):
                    app['client_secret'] = mask
                    for token in app.get('access_tokens', []):
                        token['access_token'] = mask
                        if token.get('refresh_token'):
                            token['refresh_token'] = mask
        return data

settings = Settings()
masked_settings = settings.mask_sensitive_data()
print(masked_settings)
