
# encryption/decrypt.py

import base64
import os
import sys

from pathlib import Path

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet


def decrypt_submission(encrypted_file_path, output_file=None):

    encrypted_path = Path(encrypted_file_path)

    if not encrypted_path.exists():
        raise FileNotFoundError(
            f"Encrypted submission not found: {encrypted_path}"
        )

    # Load private key from GitHub Actions secret
    private_key_b64 = os.environ.get("PRIVATE_KEY_B64")

    if not private_key_b64:
        raise ValueError(
            "Private key secret PRIVATE_KEY_B64 was not found!"
        )

    try:
        private_key_pem = base64.b64decode(
            private_key_b64,
            validate=True
        )

        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None
        )

    except Exception as error:
        raise ValueError(
            "Unable to load the private key."
        ) from error

    # Read encrypted submission
    encrypted_file_data = encrypted_path.read_bytes()

    # Determine RSA encrypted key size
    rsa_size = private_key.key_size // 8

    if len(encrypted_file_data) <= rsa_size:
        raise ValueError(
            "Encrypted submission file is incomplete."
        )

    # Separate encrypted session key and encrypted CSV
    encrypted_session_key = encrypted_file_data[:rsa_size]
    encrypted_data = encrypted_file_data[rsa_size:]

    try:
        # Decrypt session key using RSA-OAEP
        session_key = private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Decrypt CSV using Fernet
        cipher_suite = Fernet(session_key)
        decrypted_data = cipher_suite.decrypt(encrypted_data)

    except Exception as error:
        raise ValueError(
            "Unable to decrypt submission. "
            "The file may be corrupted or encrypted with another key."
        ) from error

    # Determine output filename
    if output_file is None:
        output_file = str(
            encrypted_path.with_suffix("")
        )

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save decrypted CSV
    output_path.write_bytes(decrypted_data)

    print("Fire detection submission decrypted successfully!")
    print("Output file:", output_path)


if __name__ == "__main__":

    if len(sys.argv) not in (2, 3):
        print(
            "Usage: python decrypt.py "
            "<encrypted_file> [output_file]"
        )
        sys.exit(1)

    encrypted_file = sys.argv[1]

    output_file = (
        sys.argv[2]
        if len(sys.argv) == 3
        else None
    )

    decrypt_submission(
        encrypted_file,
        output_file
    )
