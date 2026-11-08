
# encryption/encrypt.py

import os
import sys

from pathlib import Path

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet


def encrypt_submission(input_file_path):

    input_path = Path(input_file_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Submission file not found: {input_path}"
        )

    if input_path.suffix.lower() != ".csv":
        raise ValueError("Submission must be a CSV file.")

    # Get script directory
    script_dir = Path(__file__).resolve().parent

    # Load public key
    key_path = script_dir / "public_key.pem"

    if not key_path.exists():
        raise FileNotFoundError(
            f"Public key not found: {key_path}"
        )

    with key_path.open("rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read()
        )

    # Generate a random session key
    session_key = Fernet.generate_key()
    cipher_suite = Fernet(session_key)

    # Read submission CSV
    file_data = input_path.read_bytes()

    if not file_data:
        raise ValueError("Submission file is empty.")

    # Encrypt CSV using Fernet
    encrypted_data = cipher_suite.encrypt(file_data)

    # Encrypt session key using RSA-OAEP
    encrypted_session_key = public_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Save encrypted submission
    output_path = Path(str(input_path) + ".enc")

    with output_path.open("wb") as file:
        file.write(encrypted_session_key)
        file.write(encrypted_data)

    print("Fire detection submission encrypted successfully!")
    print("Output file:", output_path)


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python encrypt.py <submission.csv>")
        sys.exit(1)

    encrypt_submission(sys.argv[1])
