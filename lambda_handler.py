import os
import sys

from mangum import Mangum

# In Lambda, source code is packaged under /var/task/app.
app_root = os.path.join(os.path.dirname(__file__), "app")
if app_root not in sys.path:
    sys.path.insert(0, app_root)

from src.main import app

handler = Mangum(app, lifespan="off")
