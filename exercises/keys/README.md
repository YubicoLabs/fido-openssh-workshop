# Getting to know your security key

- Insert your security key and use `fido2-token -L` to list its device file (e.g. `/dev/hidraw0` on linux or `ioreg:n` on macOS)

- Use `fido2-token -I <device>` to get information on your security key

  - Check `options:` to see if a PIN is set (`clientPin`) or not (`noclientPin`)

  - Also check what the minimum PIN length is (`minpinlen:`)

  Note that minimum PIN length is only reported on FIDO 2.1+ security keys with libfido2 version 1.12 or later.

  - If a PIN has not been set, set a PIN using `fido2-token -S <device>`

  Note that a PIN does not have to be numeric.
  The maximum PIN length is 64.

  - What `algorithms:` does your security key support?
  `es256` corresponds to `ecdsa-sk`, `eddsa` corresponds to `ed25519-sk`

  - Verify that your security key supports user presence (`options: up`)

# Key generation

- Use `ssh-keygen` to generate a hardware-backed SSH key pair.
  Use type `ecdsa-sk` (`-t`) and store the key files locally using the name `id_ecdsa_sk `(`-f`). Do not use a passphrase (`-N`).

```
  ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk -N ''
```

Note that the passphrase doesn't make sense here. The private key is stored on the security key, not in the private key file, so there is nothing that needs encryption.

- Using your Python virtual environment, run the script in the `tools` directory to inspect the private key file:

```
  ../../tools/openssh-key-v1.py ./id_ecdsa_sk
```
Notice that it only contains a handle to the private key on your security key (it's credential ID), not the private key itself!

- Build a docker image using the Dockerfile in this directory:

```
  docker build --build-arg user=ubuntu -t ssh-server .
```

- Run the docker container:

```
  docker run --rm -d -p 22:22 --name ssh_demo ssh-server
```

If you have a local sshd running, shut it down or use a different port.

- Sign in to the SSH server using your hardware backed key:

```
  ssh -i ./id_ecdsa_sk ubuntu@localhost
```

# User Verification

- Note that when signing in, user presence was required, but not user verification (i.e. no PIN was prompted for).
Re-generate your keys with option `-O verify-required` and rebuild your server:

```
  docker stop ssh_demo
  docker build --build-arg user=ubuntu -t ssh-server .
  docker run --rm -d -p 22:22 --name ssh_demo ssh-server
```

- Sign in again and note that you are now prompted for a PIN

# Resident keys

- Use `fido2-token -I <device>` to check if your security key supports resident keys (`options: rk`)

Note: Resident keys are called discoverable credentials since FIDO 2.1, but OpenSSH still uses the older term.

- Use `fido2-token -L -r <device>` to list the resident keys on your security key.

(This list will be empty unless you had any resident keys stored prior to this workshop)

- Re-generate your keys with option `-O resident`

- Use `fido2-token -L -r <device>` to see if your new key is stored on your security key.

The columns represent an index, the SHA256 hash of your RP ID, and the RP ID itself, which defaults to `ssh:`

- Rebuild your server (see instructions above) and verify you can still sign in.

# GitHub

Now also generate a second resident key for your GitHub account.
Because a credential stored on a security key is indexed by Relying Party ID (defaulting to `ssh:` for ssh-keygen) and User ID (defaulting to 0x00... for ssh-keygen),
we need to distinguish the new resident key from the resident key already present. Otherwise, we would be overwriting our previously generated credential.

- Generate a resident key for your GitHub account using a different RP ID (option `-O application=ssh:github`).

- Use `fido2-token -L -r <device>` to see if your new key is stored on your security key.

- Use `fido2-token -L -r <device> -k ssh:github` to see resident keys specific to your GitHub application.

The columns represent an index, your credential's ID, the user display name, user ID, type and protection level.

- Register your GitHub public key at GitHub (https://github.com/settings/keys)

- Verify your key is listed as an authentication key:

```sh
  curl https://github.com/<username>.keys
```

where `<username>` is your GitHub username.

- Test SSH access to GitHub:

```sh
ssh -T git@github.com -i <identity_file>
```

# Generating key files for resident keys

If you want to use your credentials on a different system, you need to have the key files on that system.
With non-resident keys, this means copying the key files over to that new system.
With resident keys, you can regenerate the key files from data stored on your security keys.

- Instead of using a different system, simply delete all key files from your local directory.

- Restore the key files using `ssh-keygen -K`

Note that all files have been regenerated, but to prevent files from overwriting one another, the files names have a naming convention that includes the options used to create them.

- Verify that you can still authenticate to GitHub using the regenerated key files.

# Done

Clean up your docker container and image:

```
docker stop ssh_demo
docker rmi ssh-server
```

Remove the server key from your `known_hosts` file:

```
ssh-keygen -R 'localhost'
```

You can also delete the key files:

```
rm id_ecdsa_sk_rk{,_github}{,.pub}
```

If you also want to delete the resident keys from your security key, use

```
fido2-token -D -i <credential_id_hash> <device>
```

