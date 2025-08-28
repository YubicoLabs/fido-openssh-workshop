# FIDO OpenSSH Workshop
A Workshop on using FIDO Security Keys with OpenSSH.

OpenSSH has built-in support for FIDO security keys since version 8.2 (released in 2020).
This means you can protect your SSH private keys using USB security keys,
similar to how this can be done with OpenPGP smart cards and cryptographic tokens that support PKCS#11.
Although such devices all allow you to protect your private keys using cryptographic hardware,
the benefits of using FIDO security keys include:

- FIDO security keys are easier to use, especially for beginners

- security keys can also be used on the web to store passkeys

- no need for vendor-specific software (such as PKCS#11 modules)

- security keys are inexpensive

- FIDO features device attestation, which lets you cryptographically prove you are using a specific security key make and model.

In this workshop, we will give a short introduction to FIDO security keys,
and provide several exercises for the use of security keys with OpenSSH,
such as signing arbitrary data, authenticating to remote systems, and using key attestation.

The workshop consists of a number of exercises that participants can perform on their system.
Participants should bring a laptop (Linux or macOS is recommended) and a security key (any vendor will do).

## Workshop preparation

To save time downloading tools during the workshop, participants should download and install the following in advance:

- Docker Desktop (or something similar, eg podman) to run Docker containers.

	[https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

- A recent Ubuntu image. We recommend pulling the latest LTS version (24.04 when this README was last updated)
```sh
	docker pull ubuntu:latest
```

- `libfido2`, which includes some command-line tools to interact with security keys. See the following web page for installation instructions:

	[https://developers.yubico.com/libfido2/](https://developers.yubico.com/libfido2/)

- This repository, which contains some Python tools that can be useful:
```sh
	git clone https://github.com/YubicoLabs/fido-openssh-workshop.git
```

- Python 3, which is probably already installed on your system. To make sure, run
```sh
	python3 -V
```

As a minimum Python, version 3.10 is required.

### Python virtual environment

To run the python scripts in this repository, it is recommended to use a virtual environment:
```sh
	python3 -m venv venv
	source venv/bin/activate
```
to install the dependencies used:
```sh
	pip install fido2 requests PyYAML
```
