from src.utils.paths import *
from PyCameraSDK.Common import *

# Смотрим что есть в Common
depth_attrs = [attr for attr in dir() if 'DEPTH' in attr.upper() or 'depth' in attr.lower()]
print("Константы с DEPTH:", depth_attrs)

# Смотрим все константы из модуля
import PyCameraSDK.Common as common_module
all_attrs = [attr for attr in dir(common_module) if not attr.startswith('_')]
print("\nВсё из Common.py:")
for attr in all_attrs:
    val = getattr(common_module, attr)
    if not callable(val):
        print(f"  {attr} = {val}")