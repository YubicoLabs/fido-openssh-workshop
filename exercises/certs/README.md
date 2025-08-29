# LargeBlobs: storing an SSH certificate on a FIDO security key

In this exercise we are using SSH certificates to sign in to a server.
Using resident keys, we can always regenerate SSH key files.
Using largeBlobs, we can also store the certificate.

- use command `fido2-token -I <device>` to check if largeBlobs are supported on your security keys: (`options: largeBlobs`)

If your security key doesn't, ask your instructor for one that does.

- generate the CA key pair (`id_userca`, `id_userca.pub`):

```
ssh-keygen -t ecdsa -f ./id_userca -N '' -C ca@example.org
```

Note that we store the CA private key in a file, but we might just as well have generated it on a security key.

- Generate a resident SSH key on a security key (`id_ecdsa`, `id_ecdsa.pub`):

```
ssh-keygen -t ecdsa-sk -f ./id_ecdsa -N '' -O resident -O verify-required -O application=ssh:demo -O user=ubuntu -C ubuntu@example.org
```
Like before, we specify non-default user and application names to distinguish different credentials stored on the security key. 
We also add the username as a comment (`-C`) in the public key file so we can more easily distinguish public key files.

- list the credential on your security key:
```
fido2-token -L -k ssh:demo <device>
```
(Change `<device>` filename reported on your system `fido2-token -L`)
Note the (base64-encoded) credential ID.

- Now use the CA key (`id_userca`) to sign your pubkey (`id_ecdsa.pub`) into an SSH certificate (`id_ecdsa-cert.pub`):
```
ssh-keygen -s ./id_userca -I ubuntu@example.org -V +52w -n ubuntu,ubuntu@example.org id_ecdsa.pub
```
The certificate will be valid (`-V`) until 52 weeks from now, and is bound to user names (`-n`) `ubuntu` and `ubuntu@example.org`.

- View the generated certificate
```
ssh-keygen -f ./id_ecdsa-cert.pub -L
```

- Store the certificate in a largeBLob on your security key, associated with your credential for the `ssh:demo` application.
```
fido2-token -S -b -n ssh:demo id_ecdsa-cert.pub <device>
```

- List the largeBlobs on your device to verify your certificate is stored:
```
fido2-token -L -b <device>
```
The output should list a line containing an index, the sizes of stored ciphertext and the original file, respectively, 
followed by the ID of the associated credential,
and the ID of the associated Relying Party (rpID, or application as it is called in OpenSSH).

Note that the credential ID listed here matches the credential ID of your resident key listed earlier.

# Signing in using your certificate

- Build a Docker image for your SSH server:

```
docker build --build-arg user=ubuntu -t ssh-server .
```
Note that instead of copying the user's public key to their `~/.ssh` directory,
the SSH server is configured system-wide (i.e. in `/etc/ssh/sshd_config`) 
to authenticate with the CA's public key (`user_ca.pub`) 
using the `TrustedUserCAKeys` directive.

- Run a container:
```
docker run --rm -d -p 22:22 --name ssh_demo ssh-server
```

NOTE: make sure your system is not running a local SSH server (and change ports if you do)

Your SSH server should accept any public key signed by the CA.

- To verify, sign in using your certified key:
```
ssh -i ./id_ecdsa ubuntu@localhost
```

# Signing in from another system

Now, all required files are stored on your security key.
This means you only need yout security key when signing in from another system.

- To verify, instead of using another system, remove all ssh user key files, including the certificate:
```
rm id_ecdsa{,.pub,-cert.pub}
```

- without these files, you can of course no longer sign in:
```
ssh -i ./id_ecdsa ubuntu@localhost
```

- Now extract the SSH key files from your security key:
```
ssh-keygen -K -N ''
```
Note that the generated key files include the key type (`ecdsa_sk`), the fact that the key is resident (`rk`), the application suffix (`demo`), and the user name (`ubuntu`).

- Also extract the SSH certificate from your security key by retrieving the large blob (`-b`) associated with your `ssh:demo` application (`-n`), and store it in the file `id_ecdsa_sk_rk_demo_ubuntu-cert.pub`:
```
fido2-token -G -b -n ssh:demo ./id_ecdsa_sk_rk_demo_ubuntu-cert.pub <device>
```
Note that the filename `id_ecdsa_sk_rk_demo_ubuntu-cert.pub` was choosen to match the names of the files generated in the previous step.

- You should now have restored the SSH key files as well as your certificate:
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
fido2-token -D -b -n ssh:demo <device>
```

Also delete the corresponsing resident credential:

```
fido2-token -D -i $(fido2-token -L -k ssh:demo <device> | cut -d' ' -f2) <device>
```

Finally, delete the key files and certificate:
```
rm ./id_userca{,.pub} ./id_ecdsa_sk_rk_demo_ubuntu{,.pub,-cert.pub}
```
