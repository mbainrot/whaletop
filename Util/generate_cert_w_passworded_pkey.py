from OpenSSL import crypto, SSL
import time
import string
import secrets

pemPath = 'valid_encrypted.pem'

key = crypto.PKey()
key.generate_key(crypto.TYPE_RSA, 4096)

cert = crypto.X509()
cert.get_subject().C = 'AU'
cert.get_subject().ST = 'ACT'
cert.get_subject().L = 'Canberra'
cert.get_subject().O = 'Non-existant Company'
cert.get_subject().OU = 'Gadgets and Widgets Unit'
cert.get_subject().CN = 'localhost.localdomain'
cert.get_subject().emailAddress = 'null@localhost.local.domain'
cert.set_serial_number(0)
cert.gmtime_adj_notBefore(0)
cert.gmtime_adj_notAfter(3600 * 24 * 365)
cert.set_issuer(cert.get_subject())
cert.set_pubkey(key)
cert.sign(key, 'sha512')

# Dump public certificate
with open(pemPath, 'wt') as f:
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))

letter_set = string.ascii_letters + string.digits
password = ''.join(secrets.choice(letter_set) for i in range(20))

print("Generated password: %s" % password)

# Dump private key
with open(pemPath, 'at') as f:
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key,'AES-256-CBC', passphrase=password.encode('ascii')).decode("utf-8"))