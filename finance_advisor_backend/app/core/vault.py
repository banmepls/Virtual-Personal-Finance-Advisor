import os
import logging
import hvac
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")

class VaultManager:
    def __init__(self):
        self.client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
        self.master_key = None
        self._init_vault()

    def _init_vault(self):
        try:
            if not self.client.is_authenticated():
                logger.warning("Vault authentication failed. Check VAULT_TOKEN.")
                return

            # If DEV Vault is used, secrets engine is 'secret' v2 by default
            try:
                # Try to read the master key
                read_response = self.client.secrets.kv.v2.read_secret_version(
                    mount_point='secret',
                    path='finance_advisor/master_key'
                )
                self.master_key = read_response['data']['data']['key']
                logger.info("Retrieved AES master key from HashiCorp Vault.")
            except hvac.exceptions.InvalidPath:
                # Secret doesn't exist yet, generate and store
                logger.info("Master key not found in Vault. Generating a new AES-256 key...")
                new_key = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
                self.client.secrets.kv.v2.create_or_update_secret(
                    mount_point='secret',
                    path='finance_advisor/master_key',
                    secret=dict(key=new_key)
                )
                self.master_key = new_key
                logger.info("Stored new AES master key in HashiCorp Vault.")
        except Exception as e:
            logger.error(f"Error communicating with Vault: {e}")
            # Fallback for local development if Vault is completely down
            fallback_key = os.getenv("FALLBACK_MASTER_KEY", base64.urlsafe_b64encode(b'12345678901234567890123456789012').decode())
            logger.warning("Using insecure fallback master key because Vault is unreachable!")
            self.master_key = fallback_key

vault_manager = VaultManager()

def get_master_key():
    return vault_manager.master_key
