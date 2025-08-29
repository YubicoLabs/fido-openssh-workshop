#!/usr/bin/env python

import sys
import base64
import yaml
import struct

def tlvs(data):
  while data:
    t, l = struct.unpack('>hh', data[:4])
    assert t == 0
    v = data[4:4+l]
    data = data[4+l:]
    yield v

def match(data, s):
    assert( data.startswith(s) )
    return data[len(s):]

def readn(data, n):
    return data[0:n], data[n:]

def read(data):
    t, l = struct.unpack('>hh', data[:4])
    assert t == 0
    return data[4:4+l], data[4+l:]

def bits(n):
    return [] if n<1 else [ bool(n&1) ] + bits(n>>1)

def bitnames(n, names):
    return [ name for (bit,name) in zip(bits(n), names) if bit ]

flagnames = [
  'up_required',
  'undefined',
  'uv_required',
  'undefined',
  'force_operation',
  'resident_key',
]

#define SSH_SK_USER_PRESENCE_REQD       0x01
#define SSH_SK_USER_VERIFICATION_REQD   0x04
#define SSH_SK_FORCE_OPERATION          0x10
#define SSH_SK_RESIDENT_KEY             0x20

  
skfile = sys.argv[1]

with open(skfile, "rb") as f:
  contents = f.read()

if not contents.isascii():
    print(f"expecting OpenSSH private key file '{ skfile }'", file=sys.stderr)
    sys.exit(1)

lines = contents.decode('utf-8').split('\n')
if(lines[0] != '-----BEGIN OPENSSH PRIVATE KEY-----'):
    print(f"expecting OpenSSH private key file '{ skfile }'", file=sys.stderr)
    sys.exit(1)

b64 = "".join(lines[1:-2])
sshkey=base64.b64decode(b64)

def read_private_key(s):
  result = {}
  keytype,s = read(s)
  result['keytype'] = str(keytype, 'utf-8')
  match keytype:
    case b'sk-ecdsa-sha2-nistp256@openssh.com':
      curve,s = read(s)
      assert(curve == b'nistp256')
      result['curve'] = str(curve, 'utf-8')
      q,s = read(s)
      result['q'] = q.hex()
    case b'sk-ssh-ed25519@openssh.com':
      public_key,s = read(s)
      result['public_key'] = public_key.hex()
    #case b'ecdsa-sha2-nistp256':
    #case b'ssh-ed25519':
    case _:
      print(f"unsupported type '{ s.decode() }'", file=sys.stderr)
      sys.exit(1)
  app,s = read(s)
  result['app'] = str(app, 'utf-8')
  flags,s = readn(s,4)
  result['flags_hex'] = flags.hex()
  f = int.from_bytes(flags, byteorder='little')
  result['flags'] = bitnames(f, flagnames)
  length,s = readn(s,1)
  length, = struct.unpack('B', length)
  handle,s = readn(s,length)
  result['handle_hex'] = handle.hex()
  result['handle_b64'] = str(base64.b64encode(handle),'utf-8')
  null,s = read(s)
  assert(null == b'')
  comment, s = read(s)
  result['comment'] = str(comment, 'utf-8')
  return result, s

#define AUTH_MAGIC      "openssh-key-v1"
 
#	byte[]	AUTH_MAGIC
#	string	ciphername
#	string	kdfname
#	string	kdfoptions
#	uint32	number of keys N
#	string	publickey1
#	string	publickey2
#	...
#	string	publickeyN
#	string	encrypted, padded list of private keys

# For unencrypted keys the cipher "none" and the KDF "none" are used with empty passphrases. The options if the KDF "none" are the empty string.

def openssh_key_v1(s):
  result = {}
  s = match(s, b'openssh-key-v1')
  s = match(s, b'\0')
  ciphername, s = read(s)
  result['ciphername'] = str(ciphername, 'utf-8')
  kdfname, s = read(s)
  result['kdfname'] = str(kdfname, 'utf-8')
  kdfoptions, s = read(s)
  result['kdfoptions'] = kdfoptions
  result['kdfoptions_hex'] = kdfoptions.hex()
  n,s = readn(s, 4)
  number_of_keys, = struct.unpack('>i', n)
  assert(number_of_keys==1)
  pubkeys = []
  for x in range(0, number_of_keys):
    pubkey, s = read(s)
    keytype,*rest = tlvs(pubkey)
    key = { 'keytype': str(keytype, 'utf-8') }
    match keytype:
      case b'sk-ssh-ed25519@openssh.com':
        (public_key,application) = rest
        key['public_key'] = public_key.hex()
        key['app'] = str(application, 'utf-8')
        #key = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
      case b'sk-ecdsa-sha2-nistp256@openssh.com':
        (curvename,q,application) = rest
        key['curvename'] = str(curvename, 'utf-8')
        key['q'] = q.hex()
        key['app'] = str(application, 'utf-8')
        #curve = ec.SECP256R1()
        #key = ec.EllipticCurvePublicKey.from_encoded_point(curve,q)
      #case b'ecdsa-sha2-nistp256':
      #case b'ssh-ed25519':
      case _:
        print(f"unsupported key type '{ keytype.decode() }'", file=sys.stderr)
        sys.exit(1)
    pubkeys.append(key)
  result['public_keys'] = pubkeys
  private_keys, s = read(s)
  assert(s == b'')
  x = p(private_keys, number_of_keys)
  result['private_keys'] = [x]
  return { 'openssh-key-v1': result }

#########

# PROTOCOL.key

# 3. Unencrypted list of N private keys

#	uint32	checkint
#	uint32	checkint
#	byte[]	privatekey1
#	string	comment1
#	byte[]	privatekey2
#	string	comment2
#	...
#	byte[]	privatekeyN
#	string	commentN
#	byte	1
#	byte	2
#	byte	3
#	...
#	byte	padlen % 255

def p(data, number_of_keys):
  # a random integer is assigned to both checkint fields so successful decryption can be quickly checked by verifying that both checkint fields hold the same value.
  checkint1,data = readn(data,4)
  checkint2,data = readn(data,4)
  assert(checkint1 == checkint2)

  for x in range(0, number_of_keys):
    result, data = read_private_key(data)
  # padding
  padding = bytes([i+1 for i in range(len(data))])
  assert(padding == data)
  return result

openssh_keys = openssh_key_v1(sshkey)
print(yaml.dump(openssh_keys))

#print(str(base64.b64encode(handle),'utf-8'))

# credProtect is required for -O resident and -O verify-required

# 1. userVerificationOptional: "uvopt"
#	"FIDO_2_0" semantics. Default
#	performing some form of user verification is optional with or without credentialID list.
# 2. userVerificationOptionalWithCredentialIDList: "uvopt+id"
#	credential is discovered only when its credentialID is provided by the platform or when some form of user verification is performed.
# 3. userVerificationRequired: "uvreq"
#	discovery and usage of the credential MUST be preceded by some form of user verification.
