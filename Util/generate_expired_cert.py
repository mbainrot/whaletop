from OpenSSL import crypto, SSL
import time

pemPath = 'expired_combined.pem'

beforeTs = time.gmtime(time.time() - 3600 * 48)
afterTs = time.gmtime(time.time() - 3600 * 24)

notBeforeStrTs = time.strftime('%Y%m%d%H%M%SZ',beforeTs)
notAfterStrTs = time.strftime('%Y%m%d%H%M%SZ', afterTs)

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
cert.set_notBefore(notBeforeStrTs.encode('ASCII'))
cert.set_notAfter(notAfterStrTs.encode('ASCII'))
cert.set_issuer(cert.get_subject())
cert.set_pubkey(key)
cert.sign(key, 'sha512')

# Dump public certificate
with open(pemPath, 'wt') as f:
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))

# Dump private key
with open(pemPath, 'at') as f:
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8"))