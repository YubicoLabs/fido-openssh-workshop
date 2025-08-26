# FIDO device attestation: verify security key provenance

In this exercise, we look at FIDO device attestation.
This lets you prove that a FIDO credential was generated on a particular security key make and model.
This can be required by an SSH CA, that only wants to sign an SSH pubkey if there is a guarantee that the corresponding private key is under protection of a security key.


# FIDO metadata

Device attestation uses FIDO metadata to lookup specific properties of a security key.
Every security key make and model is identified by an identifier called an AAGUID.
This identifier is not unique for the device (so cannot be used to identify a specific security key),
but is specific to a specific vendor and model (typically up to its firmware version).

- Use fido-token to lookup the AAGUID for your security key.

- Lookup the metadata for your security key, based on that AAGUID, using the FIDO MDS explorer:

    https://opotonniee.github.io/fido-mds-explorer/

# Generate key and attestation

- Generate a random challenge:

```
openssl rand 128 > challenge.bin
```

The challenge must be saved in order to verify the attestation later.

- Generate a new key pair with attestation using the challenge:

```
ssh-keygen -t ecdsa-sk -f ./id -N "" -O challenge=challenge.bin -O write-attestation=attestation.bin
```

The attestation is a signed statement generated on the security key using an attestation key.
We need FIDO metadata to verify the attestation.

# Verify attestation

Note that normally, you don't need to bother with verifying attestations - you already know what security key you are using.

Verifying the attestation involves validating the attestation's signature using the attestation certificate that is also embedded on the security key,
and validating that certificate against FIDO's Metadata Service.

Let's start with obtaining a fresh copy of FIDO metadata.

```
curl -Ls https://mds.fidoalliance.org/ --output mds.jwt
```

This should generate a file `mds.jwt` with FIDO metadata.

We are using a python tool to verify the attestation agains FIDO metadata.

- To not interfere with how Python is installed on your system, create a Python virtual environment.

```
python3 -m venv venv
```

- Now activate the virtual environment:

```
source venv/bin/activate
```

- Install dependencies:

```
pip install requests fido2
```

Note: before running the Python script, inspect its contents to get an idea of what it is doing.

- Now use the python script in this directory to verify the attestation:

```
./ssh-sk-attest.py --key id.pub --attestation attestation.bin --challenge challenge.bin --mds mds.jwt
```
