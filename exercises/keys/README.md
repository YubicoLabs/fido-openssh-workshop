Run all commands in this exercise from the `exercises/keys` directory.

# Getting to know your security key

- Insert your security key and use `fido2-token -L` to list its device file (e.g. `/dev/hidraw0` on Linux or `ioreg:n` on macOS)

> **Tip:** Copy your device path from this output. You will use it for every `fido2-token` command in this exercise.

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

  - Verify that your security key supports the credProtect extension (`extension strings: credProtect`)

The `credProtect` extension is required by OpenSSH if you want to enforce user verification for your SSH keys, or when you want to create resident keys.

# Key generation

- Use `ssh-keygen` to generate a hardware-backed SSH key pair.
  Use type `ecdsa-sk` (`-t`) and store the key files locally using the name `id_ecdsa_sk` (`-f`). Do not use a passphrase (`-N`).

```sh
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk -N ''
```

You can run this from any directory. The `-f` flag saves the files wherever you currently are. Regular SSH keys normally go in `~/.ssh/`, but with FIDO keys it doesn't matter because the private key is on the security key, not in the file.

Note that a passphrase is not used here. The private key is stored on the security key, not in the private key file, so there is nothing that needs encryption.
This does mean that someone that has physical access to the security key, as well as access to the private key file,
can sign in on any server that trusts the public key.
We will see [later](#user-verification) that there is a better way to prevent this from happening.

- Using your Python virtual environment, run the script in the `tools` directory to inspect the private key file:

```sh
../../tools/openssh-key-v1.py ./id_ecdsa_sk
```
Notice that the private key file only contains a handle to the private key generated and stored on your security key (its credential ID), not the private key itself!

- Build a docker image using the Dockerfile in this directory:

```sh
docker build --build-arg user=ubuntu -t ssh-server .
```
The Dockerfile uses Ubuntu as a base image, installs OpenSSH, disables password authentication, copies the user's public key into their `.ssh/authorized_keys` file and starts the SSH server.

- Run the docker container:

```sh
docker run --rm -d -p 22:22 --name ssh_demo ssh-server
```

If you have a local sshd running, shut it down or use a different port (e.g. `-p 2222:22`, then `ssh -p 2222 ...`).

- Sign in to the SSH server using your hardware-backed key:

```sh
ssh -i ./id_ecdsa_sk ubuntu@localhost
```

Your security key will flash. Touch it to confirm user presence and complete the sign-in.

The server will allow you to sign in using your hardware-backed SSH key,
because the corresponding public key was copied into the user's `~/.ssh/authorized_keys` file
(see the [Dockerfile](Dockerfile) used to build the server).

# User Verification

Note that when signing in, user presence was required, but not user verification (i.e. no PIN was prompted for).
This means anyone that has access to both the security key and the (unencrypted) key files can sign in on your server.
Instead of encrypting the key file with a passphrase, let's use user verification.

User verification is more secure than using a passphrase, as the former is used to authenticate to the security key prior to any
signing operation, while the latter is used to derive a decryption key to load the private key into memory.
While the passphrase can be brute-forced, the security key will block when too many PIN attempts have failed.

If you want the server to require user verification when signing in,
you can do so by prepending the `verify-required` option to the entry in the `~/.ssh/authorized_keys` file.

- While signed in on your server, use your favorite text editor or `sed` to edit the `authorized_keys` key file
for the `ubuntu` user and prepend the string "`verify-required `" to the line with your public key:

```sh
sed -e 's/^/verify-required /' -i  ~/.ssh/authorized_keys
```

- Try to sign in on the server again. Notice that this is no longer allowed, since user verification was never performed.

To fix this, re-generate your keys with option `-O verify-required` and rebuild your server:

```sh
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk -N '' -O verify-required
docker stop ssh_demo
docker build --build-arg user=ubuntu -t ssh-server .
docker run --rm -d -p 22:22 --name ssh_demo ssh-server
```

- Sign in again and note that you are now prompted for a PIN

If you have a security key with built-in user verification (for instance with a fingerprint reader), you are still prompted for the PIN.
You can however enter an empty PIN, after which you can perform user verification to sign in.

# Resident keys

- Use `fido2-token -I <device>` to check if your security key supports resident keys (`options: rk`)

Note: Resident keys are called discoverable credentials since FIDO 2.1, but OpenSSH still uses the older term.

- Use `fido2-token -L -r <device>` to list the resident keys on your security key.

(This list will be empty unless you had any resident keys stored prior to this workshop)

- Re-generate your keys with option `-O resident`:

```sh
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk -N '' -O resident
```

If you are prompted that a resident key already exists, you can overwrite it.

- Use `fido2-token -L -r <device>` to see if your new key is stored on your security key.

The columns represent an index, the SHA256 hash of your RP ID, and the RP ID itself, which defaults to `ssh:`

- Rebuild your server and verify you can still sign in:

```sh
docker stop ssh_demo
docker build --build-arg user=ubuntu -t ssh-server .
docker run --rm -d -p 22:22 --name ssh_demo ssh-server
ssh -i ./id_ecdsa_sk ubuntu@localhost
```

# GitHub

Now also generate a second resident key for your GitHub account.
Because a credential stored on a security key is indexed by Relying Party ID (defaulting to `ssh:` for ssh-keygen) and User ID (defaulting to 0x00... for ssh-keygen),
we need to distinguish the new resident key from the resident key already present. Otherwise, we would be overwriting our previously generated credential.

- Generate a resident key for your GitHub account using a different RP ID (option `-O application=ssh:github`):

```sh
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk_github -N '' -O resident -O application=ssh:github
```

- Use `fido2-token -L -r <device>` to see if your new key is stored on your security key. You should see a new entry with RP ID `ssh:github`.

- Use `fido2-token -L -r <device> -k ssh:github` to see resident keys specific to your GitHub application.

The columns represent an index, your credential's ID, the user display name, user ID, type and protection level.

- View your public key and copy it:

```sh
cat ./id_ecdsa_sk_github.pub
```

- Register this public key at GitHub (https://github.com/settings/keys). Click "New SSH key", set the type to "Authentication Key", and paste the full public key line.

- Verify your key is listed as an authentication key:

```sh
curl https://github.com/<username>.keys
```

where `<username>` is your GitHub username (e.g. `curl https://github.com/johndoe.keys`).

- Test SSH access to GitHub:

```sh
ssh -T git@github.com -i ./id_ecdsa_sk_github
```

You should see: `Hi <username>! You've successfully authenticated, but GitHub does not provide shell access.`

# Generating key files for resident keys

If you want to use your credentials on a different system, you need to have the key files on that system.
With non-resident keys, this means copying the key files over to that new system.
With resident keys, you can regenerate the key files from data stored on your security keys.

- Instead of using a different system, simply delete all key files from your local directory:

```sh
rm ./id_ecdsa_sk{,.pub} ./id_ecdsa_sk_github{,.pub}
```

- Restore the key files using `ssh-keygen -K`

```sh
ssh-keygen -K
```

Note that all files have been regenerated, but to prevent files from overwriting one another, the file names follow a naming convention that includes the options used to create them. Use the filenames from the output for subsequent commands.

- Verify that you can still authenticate to GitHub using the regenerated key files:

```sh
ssh -T git@github.com -i ./id_ecdsa_sk_rk_github_<hash>
```

Replace the filename with the actual `ssh:github` filename printed by `ssh-keygen -K` above.

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
rm id_ecdsa_sk_rk{,_github}*
```

If you also want to delete the resident keys from your security key, use

```
fido2-token -D -i <credential_id_hash> <device>
```
