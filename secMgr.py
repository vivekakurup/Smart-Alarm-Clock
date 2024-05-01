"""
Secrets manager helper functions

2024
"""
import os
import sys
import machine
# import the micropython AES implementation
from cryptolib import aes
class SecretsManager:
    """
    Use this class to manage secrets for your project.

    Implemented as a context manager,

    example:

    with SecretsManager(b'global key') as secrets:
        secrets.ssid = b'wifi ssid'
        secrets.pwd = b'wifi password'

    with SecretsManager(b'global key') as secrets:
        wlan.connect(secrets.ssid, secrets.pwd)


    """
    def __init__(self, global_key, filename = 'secret.py'):
        self.filename = filename
        self.global_key = global_key
        self.device_key = self.generate_device_key()

        self.ck = SecretsManager.pad(self.global_key + self.device_key)
        self.secrets = {}

        self.load_secrets()

    # access secrets as properties, decrypting and encrypting as needed
    def __getitem__(self, key):
        try:
            return self.decrypt_value(self.secrets[key])
        except ValueError as e:
            # if we fail to decrypt, return the encrypted value
            return self.secrets[key]

    # you can also set secrets, store the encrypted value
    def __setitem__(self, key, value):
        ev = self.encrypt_value(value)
        self.secrets[key] = ev

    # delete secrets
    def __delitem__(self, key):
        del self.secrets[key]

    # list the keys
    def keys(self):
        return self.secrets.keys()

    # context manager
    def __enter__(self):
        return self

    # context manager
    def __exit__(self, exc_type, exc_value, traceback):
        self.save_secrets()

    # the device portion of the encryption key
    def generate_device_key(self):
        return machine.unique_id()

    # save the secrets to the file
    def save_secrets(self):
        with open(self.filename, 'w') as f:
            for key, value in self.secrets.items():
                f.write(f"{key} = {value}\n")

    # load the secrets from the file
    def load_secrets(self):
        if self.filename not in os.listdir():
            return
        with open(self.filename, 'r') as f:
            for line in f:
                line = line.strip()
                key, value = line.split('=',1)
                # the value is already encrypted, so just store it in the secrets dictionary
                self.secrets[key.strip()] = eval(value.strip())

    # simple PKCS7 unpadding (no error checking!)
    def unpad(s):
        # the last byte is the number of padding bytes
        return s[:-s[-1]]

    # simple PKCS7 padding
    def pad(s, block_size=32):
        # the last byte is the number of padding bytes, repeated
        n = block_size - (len(s) % block_size)
        if n == 0:
            n = block_size
        return s + bytes([n] * n)

    def encrypt_value(self, value):
        cipher = aes(self.ck, 1)
        return cipher.encrypt(SecretsManager.pad(value.encode('utf-8')))

    def decrypt_value(self, value):
        cipher = aes(self.ck, 1)
        pt = cipher.decrypt(value)
        return SecretsManager.unpad(pt).decode('utf-8')

if __name__ == "__main__":

    # when run, create or view secrets
    print ("Welcome to the secrets manager.")
    print ("You can use this script to create or view secrets.")
    print("-"*40)

    # input doesn't work in micropython...
    create = False

    if create:
        print ("Creating secrets...")
        with SecretsManager(b'global key', filename='secret.py') as secrets:
            secrets['ssid']     = ""
            secrets['password'] = ""
        print("Secrets saved to secret.py.")
        print("-"*40)

    # view the secrets
    print ("Viewing secrets...")
    with SecretsManager(b'global key', filename='secret.py') as secrets:
        for key in secrets.keys():
            print(f"{key} = {secrets[key]}")
