#!/usr/bin/env python

# verify attestation information to cryptographically prove that a given key is hardware-backed. 
# For instance:
#
# ./ssh-sk-attest.py --key ./id_ecdsa_sk.pub --attestation attestation.bin --challenge challenge.bin --mds mds.jwt

# To generate an SSH pubkey, a challenge, and an attestation:
# openssl rand 128 > challenge.bin
# ssh-keygen -t ${KEYTYPE} -f ./id_ecdsa_sk -N "" -O challenge=challenge.bin -O write-attestation=attestation.bin
#
# use OpenSSH 8.4 or later
# KEYTYPE can be "ecdsa-sk" or "ed25519-sk"

# This script requires FIDO Metadata to validate attestation certificates
# Download an mds blob from the FIDO Alliance:
#
# curl -Ls https://mds3.fidoalliance.org/ --output mds.jwt

# This script requires
#   requests - for downloading MDS3 metadata
#   fido2 - Yubico's FIDO 2 library to process attestations
# install using pip:
#   pip install fido2 requests
#
# TODO: use the official OpenSSH tool, once it is included in distributions
# https://github.com/openssh/openssh-portable/blob/master/regress/misc/ssh-verify-attestation/ssh-verify-attestation.c

import sys
import argparse
import requests
from base64 import b64decode
from struct import unpack
from hashlib import sha256

from fido2 import cbor, mds3, webauthn, cose
from cryptography import x509, exceptions
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519

# read a list of type-length-value triplets from binary data
def tlvs(data):
    while data:
        t, l = unpack('>hh', data[:4])
        assert t == 0
        v = data[4:4+l]
        data = data[4+l:]
        yield v

# attestation information format, see
# https://github.com/openssh/openssh-portable/blob/master/PROTOCOL.u2f
#
# string		"ssh-sk-attest-v01"
# string		attestation certificate
# string		enrollment signature
# string		authenticator data (CBOR encoded)
# uint32		reserved flags
# string		reserved string

# parse SSH attestation file 
def parseAttestation(s):
    version, certificate, signature, authData, reserved_flags, reserved_string  = tlvs(s)
    version = str(version, 'utf-8')
    assert version == 'ssh-sk-attest-v01'
    certificate = x509.load_der_x509_certificate(certificate)
    authData = cbor.decode(authData)
    assert reserved_flags== b''
    assert reserved_string == b''
    return dict( version=version, certificate=certificate, signature=signature, authData=authData)

def verifyAttestation(attestation, challenge):
    authData = attestation['authData']
    clientDataHash = sha256(challenge).digest()
    signedData = b''.join([authData, clientDataHash])
    signature = attestation['signature']
    attestation_certificate = attestation['certificate']
    assert isinstance( attestation_certificate.public_key(), ec.EllipticCurvePublicKey )
    attestation_certificate.public_key().verify(signature, signedData, ec.ECDSA(hashes.SHA256()))

def verifyAttestationU2F(attestation, challenge):
    authData = webauthn.AuthenticatorData(attestation['authData'])
    credentialData = authData.credential_data
    key = b''.join([b'\04', credentialData.public_key[-2], credentialData.public_key[-3]])
    signedData = b''.join([b'\00', authData.rp_id_hash, sha256(challenge).digest(), credentialData.credential_id, key])
    signature = attestation['signature']
    attestation_certificate = attestation['certificate']
    assert isinstance( attestation_certificate.public_key(), ec.EllipticCurvePublicKey )
    attestation_certificate.public_key().verify(signature, signedData, ec.ECDSA(hashes.SHA256()))

# parse SSH pubkey file
# https://github.com/openssh/openssh-portable/blob/master/PROTOCOL.u2f

def parsePubkey(key):
    key_type, pubkey, *_ = key.split(" ")
    key=b64decode(pubkey)
    match key_type:
        # The format of a sk-ecdsa-sha2-nistp256@openssh.com public key is:
        #	string		"sk-ecdsa-sha2-nistp256@openssh.com"
        #	string		curve name
        #	ec_point	Q
        #	string		application (user-specified, but typically "ssh:")
        case 'sk-ecdsa-sha2-nistp256@openssh.com':
            (kt,curve_name,ec_point,*application) = tlvs(key)
            assert str(kt,'utf-8') == key_type
            publicKey = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ec_point)
            return cose.ES256.from_cryptography_key(publicKey)
        # The format of a sk-ssh-ed25519@openssh.com public key is:
        #	string		"sk-ssh-ed25519@openssh.com"
        #	string		public key
        #	string		application (user-specified, but typically "ssh:")
        case 'sk-ssh-ed25519@openssh.com':
            (kt,pk,*application) = tlvs(key)
            assert str(kt,'utf-8') == key_type
            publicKey = ed25519.Ed25519PublicKey.from_public_bytes(pk)
            return cose.EdDSA.from_cryptography_key(publicKey)
        case _:
            raise Exception('unsupported SSH key type')

# the fido alliance metadata URL
mdsurl = 'https://mds3.fidoalliance.org/'
# the root CA used to verify the FIDO Metadata Statement blob
MDS_CA = b64decode(
    """
MIIDXzCCAkegAwIBAgILBAAAAAABIVhTCKIwDQYJKoZIhvcNAQELBQAwTDEgMB4G
A1UECxMXR2xvYmFsU2lnbiBSb290IENBIC0gUjMxEzARBgNVBAoTCkdsb2JhbFNp
Z24xEzARBgNVBAMTCkdsb2JhbFNpZ24wHhcNMDkwMzE4MTAwMDAwWhcNMjkwMzE4
MTAwMDAwWjBMMSAwHgYDVQQLExdHbG9iYWxTaWduIFJvb3QgQ0EgLSBSMzETMBEG
A1UEChMKR2xvYmFsU2lnbjETMBEGA1UEAxMKR2xvYmFsU2lnbjCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBAMwldpB5BngiFvXAg7aEyiie/QV2EcWtiHL8
RgJDx7KKnQRfJMsuS+FggkbhUqsMgUdwbN1k0ev1LKMPgj0MK66X17YUhhB5uzsT
gHeMCOFJ0mpiLx9e+pZo34knlTifBtc+ycsmWQ1z3rDI6SYOgxXG71uL0gRgykmm
KPZpO/bLyCiR5Z2KYVc3rHQU3HTgOu5yLy6c+9C7v/U9AOEGM+iCK65TpjoWc4zd
QQ4gOsC0p6Hpsk+QLjJg6VfLuQSSaGjlOCZgdbKfd/+RFO+uIEn8rUAVSNECMWEZ
XriX7613t2Saer9fwRPvm2L7DWzgVGkWqQPabumDk3F2xmmFghcCAwEAAaNCMEAw
DgYDVR0PAQH/BAQDAgEGMA8GA1UdEwEB/wQFMAMBAf8wHQYDVR0OBBYEFI/wS3+o
LkUkrk1Q+mOai97i3Ru8MA0GCSqGSIb3DQEBCwUAA4IBAQBLQNvAUKr+yAzv95ZU
RUm7lgAJQayzE4aGKAczymvmdLm6AC2upArT9fHxD4q/c2dKg8dEe3jgr25sbwMp
jjM5RcOO5LlXbKr8EpbsU8Yt5CRsuZRj+9xTaGdWPoO4zzUhw8lo/s7awlOqzJCK
6fBdRoyV3XpYKBovHd7NADdBj+1EbddTKJd+82cEHhXXipa0095MJ6RMG3NzdvQX
mcIfeg7jLQitChws/zyrVQ4PkX4268NXSb7hLi18YIvDQVETI53O9zJrlAGomecs
Mx86OyXShkDOOyyGeMlhLxS67ttVb9+E7gUJTb0o2HLO02JQZR7rkpeDMdmztcpH
WD9f"""
)

def getMetadata(file=None):
    if file:
    	with open(file, "rb") as f:
            data = f.read()
    else:
        response = requests.get(mdsurl, allow_redirects=True)
        data = response.content
    return mds3.parse_blob(data, MDS_CA)

# verify if an SSH key has hardware key protection by verifying its attestation
# currently only works for SSH keys backed by FIDO security keys
#
# procedure - given an SSH public key and its attestation:
# 1. verify attestation signature using attestation certificate
# 2. match SSH public key with key in attestation
# 3. extract AAGUID and lookup authenticator metadata using FIDO Metadata Service
# 4. validate attestation certificate using registered root certificates,
#    or using provided issuer certificate
# 5. check metadata for hardware and secure_element key protection
# 6. check metadata for on_chip matcher protection

# process command line arguments

parser = argparse.ArgumentParser(description='evaluate an SSH SK attestation')
parser.add_argument('-k', '--key', dest='key_file', default = 'id_ecdsa_sk.pub', help='specify SSH pubkey file to validate attestation for')
parser.add_argument('-a', '--attestation', dest='attestation_file', default = 'attestation.bin', help='specify attestation file')
parser.add_argument('-c', '--challenge', dest='challenge_file', default = 'challenge.bin', help='specify challenge file')
parser.add_argument('-m', '--mds', dest='mds_file', help='specify MDS JWT file')
parser.add_argument('-i', '--issuer', dest='issuer_file', help='specify PEM-encoded issuer certificate file for validating attestation certificate')
args = parser.parse_args()

try:
    with open(args.key_file, mode='r') as f:
        publicKey = parsePubkey(f.read())
except FileNotFoundError:
    print(f"❌ SSH pubkey file not found ({args.key_file}), use --key FILE to specify SSH pubkey file to use", file=sys.stderr)
    sys.exit(1)
except AssertionError:
    print(f"❌ SSH pubkey file malformed ({args.key_file})", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"❌ {e}", file=sys.stderr)
    sys.exit(1)

try:
    with open(args.attestation_file, mode='rb') as f:
        attestation = parseAttestation(f.read())
except AssertionError:
    print(f"❌ Attestation file malformed ({args.attestation_file})", file=sys.stderr)
    sys.exit(1)
except FileNotFoundError:
    print(f"❌ Attestation file not found ({args.attestation_file}), use --attestation FILE to specify attestation file to use", file=sys.stderr)
    sys.exit(1)

try:
    with open(args.challenge_file, mode='rb') as f:
        challenge = f.read()
except FileNotFoundError:
    print(f"❌ Challenge file not found ({args.challenge_file}), use --challenge FILE to specify attestation file to use", file=sys.stderr)
    sys.exit(1)

# verify attestation signature, assuming packed attestation
try:
    verifyAttestation(attestation, challenge) 
except AssertionError:
    print(f"❌ Attestation certificate uses an unsupported key type", file=sys.stderr)
    sys.exit(1)
except exceptions.InvalidSignature:
    # Invalid packed attestation signature, retry with fido-u2f
    try:
        verifyAttestationU2F(attestation, challenge) 
    except exceptions.InvalidSignature:
        print("❌ Invalid attestation signature, or unsupported attestation format", file=sys.stderr)
        sys.exit(1)

issuer = None
if args.issuer_file != None:
    try:
        with open(args.issuer_file, mode='r') as f:
            issuer = x509.load_pem_x509_certificate(str.encode(f.read()),default_backend())
    except FileNotFoundError:
        print(f"❌ Issuer file not found ({args.issuer_file})", file=sys.stderr)
        sys.exit(1)

# match public keys
credentialData = webauthn.AuthenticatorData(attestation['authData']).credential_data
if credentialData.public_key != publicKey:
    print(f"❌ Public key in {args.key_file} does not match public key in attestation")
    print(credentialData.public_key[-2].hex())
    print(credentialData.public_key[-3].hex())
    print(publicKey[-2].hex())
    print(publicKey[-3].hex())
    sys.exit(1)

# lookup metadata in MDS
metadata_entry = None
try:
    if(credentialData.aaguid == webauthn.Aaguid.NONE):
        print('❗ No AAGUID present in attestation, cannot lookup metadata', file=sys.stderr)
    else:
        if not args.mds_file:
            print(f"❗ No MDS blob specified, downloading from {mdsurl} ", file=sys.stderr)
        metadata = getMetadata(args.mds_file)
        metadata_entry = mds3.MdsAttestationVerifier(metadata).find_entry_by_aaguid(credentialData.aaguid)
except ValueError:
    print(f"❌ FIDO Metadata file malformed ({args.mds_file or mdsurl})", file=sys.stderr)
    sys.exit(1)
except FileNotFoundError:
    print(f"❌ FIDO Metadata file not found ({args.mds_file})", file=sys.stderr)
    sys.exit(1)

# validate attestation certificate
try:
    attestation_certificate = attestation['certificate']
    # validate attestation certificate using registered root certificates
    if issuer != None:	# use explicitly trusted certificate
        issuers = [issuer]
    elif metadata_entry:	# use roots from MDS
        issuers = [ x509.load_der_x509_certificate(cert, default_backend()) for cert in metadata_entry.metadata_statement.attestation_root_certificates ]
    else:	# no issuers, fail
        issuers = []
    trusted = False
    for cert in issuers:
        if cert.subject == attestation_certificate.issuer:
            attestation_certificate.verify_directly_issued_by(cert)
            trusted = True
    if not trusted:
        print(f"❌ Cannot validate attestation certificate ({attestation_certificate.subject.rfc4514_string({x509.oid.NameOID.EMAIL_ADDRESS: 'E'})}) is not signed by a trusted issuer", file=sys.stderr)
        sys.exit(1)
except exceptions.InvalidSignature:
    print('❌ Invalid signature on attestation certificate', file=sys.stderr)
    sys.exit(1)
except ValueError:
    print(f"❌ Invalid issuer certificate ({cert.subject.rfc4514_string({x509.oid.NameOID.EMAIL_ADDRESS: 'E'})})", file=sys.stderr)
    sys.exit(1)
except TypeError:
    print(f"❌ Unsupported issuer public key type ({cert.public_key()})", file=sys.stderr)
    sys.exit(1)

if metadata_entry:
        status_list = [s.status for s in metadata_entry.status_reports]
        if 'FIDO_CERTIFIED' not in status_list:
            print(f"❌ Security key is not FIDO certified ({ ', '.join(status_list) })", file=sys.stderr)
            sys.exit(1)

        # https://fidoalliance.org/specs/common-specs/fido-registry-v2.2-ps-20220523.html#key-protection-types
        # software, hardware, tee, secure_element, remote_handle
        if 'hardware' in metadata_entry.metadata_statement.key_protection:
            if 'secure_element' not in metadata_entry.metadata_statement.key_protection:
                print(f"➖ security key has hardware key protection but not using a secure element ({metadata_entry.metadata_statement.key_protection})", file=sys.stderr)
        else:
            print(f"➖ security key has no hardware key protection ({metadata_entry.metadata_statement.key_protection})", file=sys.stderr)

        # https://fidoalliance.org/specs/common-specs/fido-registry-v2.2-ps-20220523.html#matcher-protection-types
        # software, tee, on_chip
        if 'on_chip' not in metadata_entry.metadata_statement.matcher_protection:
            print(f"➖ security key has no on_chip matcher protection ({metadata_entry.metadata_statement.key_protection})", file=sys.stderr)

if metadata_entry:
        print(f"✅ valid attestation for hardware authenticator ({credentialData.aaguid}): {metadata_entry.metadata_statement.description}", file=sys.stderr)
elif args.issuer_file:
        print(f"✅ valid attestation for authenticator with issuer {issuer.subject.rfc4514_string({x509.oid.NameOID.EMAIL_ADDRESS: 'E'})}", file=sys.stderr)
else:
        print(f"✅ valid attestation for unknown authenticator", file=sys.stderr)
