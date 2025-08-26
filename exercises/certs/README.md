# LargeBlobs: storing an SSH certificate on a FIDO security key

In this exercise we are using SSH certificates to sign in to a server.
Using resident keys, we can always regenerate SSH key files.
Using largeBlobs, we can also store the certificate.

- check if largeBlobs are supported on your security keys: (option `largeBlobs`)

If your security key doesn't, ask your instructor for one that does.

- generate the CA key pair (id_userca, id_userca.pub):

```
ssh-keygen -t ecdsa -f id_userca -N '' -C ca@example.org
```

Note that we store the CA private key in a file, but we might just as well have generated it on a security key.

- Generate a resident SSH key on a security key (id_ecdsa, id_ecdsa.pub):

```
ssh-keygen -t ecdsa-sk -f ./id_ecdsa -N '' -O resident -O verify-required -O application=ssh:demo -O user=ubuntu -C ubuntu@example.org
```

- Now have the CA sign your pubkey (id_ecdsa.pub) into a SSH certificate, using CA key id_userca:

```
ssh-keygen -s ./id_userca -I ubuntu@example.org -V +52w -n ubuntu,ubuntu@example.org id_ecdsa.pub
```

- Store the certificate in a largeBLob on your security key

```
fido2-token -S -b -n ssh:demo id_ecdsa-cert.pub /dev/hidrawN
```

(Change the device filename are reported on your system)

- View the generated certificate

```
ssh-keygen -f id_ecdsa-cert.pub -L
```

- list the credential on your security key:

```
fido2-token -L -k ssh:demo /dev/hidrawN
```

- list the largeBlobs on your security key

```
fido2-token -L -b /dev/hidrawN
```

- Build the Docker image

```
docker build --build-arg user=ubuntu -t ssh-server .
```

- Run a container

```
docker run --rm -d -p 22:22 --name ssh_demo ssh-server
```

NOTE: make sure your system is not running a local SSH server (and change ports if you do)

Your SSH server should accept any public key signed by the CA.

- sign in using your certified key:

```
ssh -i ./id_ecdsa ubuntu@localhost
```

Now, all required files are stored on your security key.

- To verify, remove all ssh user files:

```
rm id_ecdsa{,.pub,-cert.pub}
```

- without these files, verify you can no longer sign in:

```
ssh -i ./id_ecdsa ubuntu@localhost
```

- Now extract the SSH key files from your security key

```
ssh-keygen -K -N ''
```

- Also extract the SSH certificate from your security key by retrieving the large blob:

```
fido2-token -G -b -n ssh:demo id_ecdsa_sk_rk_demo_ubuntu-cert.pub /dev/hidrawN
```

- You should now have restored both SSH key files and your certificate:

```
ls -l ./id_ecdsa*
```

- To verify, sign in using the restored files:

```
ssh -i ./id_ecdsa_sk_rk_demo_ubuntu ubuntu@localhost
```

# cleaning up

As before, clean up the docker container and image:

```
docker stop ssh_demo
docker rmi ssh-server
ssh-keygen -R 'localhost'
```

Optionally, also delete the largeblob from your security key:

```
fido2-token -D -b -n ssh:demo /dev/hidrawN
```

Finally, delete the resident credential:

```
fido2-token -D -i $(fido2-token -Lk ssh:demo /dev/hidrawN | cut -d' ' -f2) /dev/hidrawN
```
