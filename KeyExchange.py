import os

import tinyec.ec as ec
import tinyec.registry as reg

from Common import *
from Certificate import ASN1, Certificate

elliptic_curves = {
	"0017": "secp256r1",
	"0018": "secp384r1"
}

class RSA_Key_Exchange:
	def __init__(self, certificate):
		self.certificate = certificate

	def get_premaster_secret(self):
		self.premaster_secret = TLS_VERSION + os.urandom(46)
		return bytes_to_int(self.premaster_secret)

	def get_client_key_exchange(self):
		premaster_secret = b'\x00\x02' + b'\x42' * (256 - 3 - len(self.premaster_secret)) + b'\x00' + self.premaster_secret
		
		encrypted_premaster_secret = pow(bytes_to_int(premaster_secret), self.certificate.RSA_e, self.certificate.RSA_n)
		msg = hex_to_bytes('100001020100') + nb_to_bytes(encrypted_premaster_secret)
		return msg


class DHE_RSA_Key_Exchange:
	def __init__(self, server_key_exchange):
		self.p = bytes_to_int(server_key_exchange[6:6+256])
		self.y_s = bytes_to_int(server_key_exchange[11+256:11+512])
		self.g = 2
	
	def get_premaster_secret(self):
		self.x = hex_to_bytes('aedebc6285eb3c2a8b949bf3c89d5ab93ef67b13aaa2e6a4b849b48d07889ee7')
		self.y_c = pow(self.g, bytes_to_int(self.x), self.p)
		self.premaster_secret = pow(self.y_s, bytes_to_int(self.x), self.p)
		return self.premaster_secret

	def get_client_key_exchange(self):
		client_key_exchange = hex_to_bytes('100001020100') + nb_to_bytes(self.y_c)
		return client_key_exchange


class ECDHE_RSA_Key_Exchange:
	def __init__(self, server_key_exchange):
		curve_code = bytes_to_hex(server_key_exchange[5:7])
		print('Elliptic curve: ' + elliptic_curves[curve_code])
		self.curve = reg.get_curve(elliptic_curves[curve_code])
		x = bytes_to_int(server_key_exchange[9:9+32])
		y = bytes_to_int(server_key_exchange[9+32:9+64])
		self.server_pubKey = ec.Point(self.curve, x, y)

	def get_premaster_secret(self):
		self.client_secret = 0xaedebc6285eb3c2a8b949bf3c89d5ab93ef67b13aaa2e6a4b849b48d07889ee7
		self.client_pubKey = self.curve.g * self.client_secret

		secret = self.server_pubKey * self.client_secret
		return secret.x

	def get_client_key_exchange(self):
		client_key_exchange = hex_to_bytes('100000424104') + nb_to_n_bytes(self.client_pubKey.x, 32) + nb_to_n_bytes(self.client_pubKey.y, 32)
		return client_key_exchange
