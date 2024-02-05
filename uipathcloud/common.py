
from enum import Enum

from pydantic import BaseModel
from typing import Dict, Any
#from .config import Settings #circular import error

class Tags(Enum):
    items = ["items"]
    users = ["users"]
    decommission = ["decommission", "teardown", "remove", "delete"]


class SecureDumpModel(BaseModel):
    """
    A base model class designed for secure data handling and serialization,
    particularly focusing on masking sensitive information such as credentials
    before logging or dumping the data structure for debugging or informational purposes.
    
    This class provides functionality to recursively mask specified fields
    across nested models and dictionaries, ensuring that sensitive data
    is not inadvertently exposed.
    
    Usage:
        Subclass SecureDumpModel for your Pydantic models and define sensitive fields.
        Use the mask_sensitive_data method to generate a sanitized version of the data,
        with sensitive fields masked, before logging or serializing.
    """
    
    def mask_sensitive_data(self, mask: str = "******") -> Dict[str, Any]:
        """
        Masks sensitive fields in the model and any nested models or dictionaries,
        replacing sensitive data with a specified mask string.
        
        Parameters:
            mask (str): The mask string to replace sensitive information with. Default is "******".
        
        Returns:
            Dict[str, Any]: A dictionary representation of the model with sensitive fields masked.
        
        Example:
            >>> model = SecureDumpModel(client_id="123", client_secret="secret")
            >>> print(model.mask_sensitive_data())
            {'client_id': '******', 'client_secret': '******'}
        """
        masked_data = {}
        for field_name, field_value in self:
            if field_name in {"client_id", "client_secret"}:
                masked_data[field_name] = mask
            elif isinstance(field_value, list):
                masked_list = []
                for item in field_value:
                    if isinstance(item, SecureDumpModel):
                        masked_list.append(item.mask_sensitive_data(mask=mask))
                    elif isinstance(item, dict):
                        masked_item = {k: mask if k in {"client_id", "client_secret"} else v for k, v in item.items()}
                        masked_list.append(masked_item)
                masked_data[field_name] = masked_list
            elif isinstance(field_value, SecureDumpModel):
                masked_data[field_name] = field_value.mask_sensitive_data(mask=mask)
            else:
                masked_data[field_name] = field_value
        return masked_data
