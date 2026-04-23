from __future__ import annotations

import asyncio
import os
import sys
import warnings


if os.getenv("HOTEL_INTEL_USE_SELECTOR_LOOP") == "1" and sys.platform.startswith("win"):
    policy_factory = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if policy_factory is not None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            asyncio.set_event_loop_policy(policy_factory())
