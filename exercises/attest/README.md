# FIDO device attestation: verify security key provenance

In this exercise, we look at FIDO device attestation.
This lets you prove that a FIDO credential was generated on a particular security key make and model.

Note that in some cases, you don't need to bother with attestations - you already know what security key you are using to sign into servers you control.
But in other cases where an entity that authenticates users or verifies signatures using a public key wants to make sure the corresponding private key is well-protected and non-exportable.

This can for instance be used by a company's SSH CA, that only wants to sign SSH pubkeys for its users if there is proof that the corresponding private key is under protection of a security key.
Or, it can be used by the owner of a Git repository, that only wants to merge a pull requests if all commits are signed using a security key by a user they trust.

# FIDO metadata

Device attestation uses FIDO metadata to lookup specific properties of a security key.
Every security key make and model is identified by an identifier called an AAGUID.
This identifier is not unique for the device (so cannot be used to identify a specific security key),
but is specific to a vendor and model (typically up to its firmware version).

- Use `fido2-token` to lookup the AAGUID for your security key.

Security key vendors can register metadata for their devices with the FIDO Alliance in the 
[FIDO Metadata Service (MDS)](https://fidoalliance.org/metadata/).

- Lookup the metadata for your security key, based on that AAGUID, using the FIDO MDS explorer:

    https://opotonniee.github.io/fido-mds-explorer/

Note that the FIDO MDS explorer is not an official service by the FIDO Alliance,
it is just a user-readable rendering of it. The actual MDS metadata is a signed document intended for machine processing.

# Generate key and attestation

- To generate an attestation, we first need to generate a random challenge:

```
openssl rand 128 > challenge.bin
```

The challenge must be saved in order to verify the attestation later.

- Generate a new key pair with attestation using the challenge:

```
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk -N "" -O challenge=challenge.bin -O write-attestation=attestation.bin
```

The attestation is a signed statement generated on the security key using an attestation key.
This attestation key is factory-programmed and cannot be exported.
It is accompanied by an X.509 certificate issued by the security key vendor.
These vendor certificates are collected in MDS.

So, we will be using FIDO metadata to verify the attestation.

# Verify attestation

Verifying the attestation involves validating the attestation's signature using the attestation certificate that is also embedded on the security key,
and validating that certificate against FIDO's Metadata Service.

Let's start with obtaining a fresh copy of FIDO metadata.

```
curl -Ls https://mds.fidoalliance.org/ --output mds.jwt
```

This should generate a file `mds.jwt` with FIDO metadata.

We are using a python tool to verify the attestation agains FIDO metadata.

- To run this tool, first create a Python virtual environment - see the instructions here:

[../../tools/README.md](../../tools/README.md)

Note: before running the Python script, inspect its contents to get an idea of what it is doing.

- Now use the tool to verify the attestation:

```
../../tools/ssh-sk-attest.py --key id_ecdsa_sk.pub --attestation attestation.bin --challenge challenge.bin --mds mds.jwt
```

the tool does the following:

- parse the attestation generated on the security key
- verify the attestation signature
- verify the public key in the attestation matches the public key in the SSH public key file
- retrieve the FIDO metadata from MDS
- verify the signature on MDS metadata
- extract the metadata for the security key used based on the AAGUID in the attestation
- validate the attestation certificate against the issuers listed in the extracted metadata
- issue a warning if the security key is not FIDO certified, has no hardware protection

If all checks pass, the security key AAGUID and description are printed without warnings.
