from django.conf import settings

from typing import ContextManager

# Disable silk profiler based on settings
if not settings.DEBUG:
    from contextlib import nullcontext

    def silk_profiler(name=None) -> ContextManager:
        return nullcontext()

else:
    from silk.profiling.profiler import silk_profile as silk_profiler
