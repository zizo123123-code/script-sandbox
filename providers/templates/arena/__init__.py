# -*- coding: utf-8 -*-
"""Arena.ai provider template.

The package is intentionally non-functional. It provides a safe, inspectable
contract for a future Arena.ai adapter without pretending that this repository
has an Arena API integration.
"""

from .provider import ArenaProvider, get_provider

__all__ = ["ArenaProvider", "get_provider"]
__provider_id__ = "arena"
__version__ = "0.1.0"
__status__ = "template_disabled"
