import os
from dotenv import load_dotenv
import subprocess

# Load .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

# Run Meltano
try:
    subprocess.run(
        ["meltano", "run", "tap-shopify", "target-s3-csv"],
        check=True,
        env=os.environ,  # Pass loaded environment variables to subprocess
    )
except subprocess.CalledProcessError as e:
    print(f"Error running Meltano: {e}")