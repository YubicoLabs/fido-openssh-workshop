Run all commands in this exercise from the `exercises/sign` directory.

# Signing

In this exercise we will use hardware-backed SSH keys to generate digital signatures.

- Generate a new signing key:

```
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk_sign -C 'signing key' -N '' -O verify-required
```

- Test your key by signing a dummy message:

```
echo I owe you a drink > message
ssh-keygen -Y sign -f ./id_ecdsa_sk_sign -n test message
```

Note that the signature is written to the file `message.sig`.
The `test` namespace is used to distinguish between different signing domains.

- To verify signatures, we first need to specify the public keys we trust in a separate file:

```
echo -n 'johndoe@example.org ' > ./allowed_signers
cat ./id_ecdsa_sk_sign.pub >> ./allowed_signers
```

So the `allowed_signers` file contains a list of SSH user IDs and their public keys.

- To verify the signature, refer to the signer identity and the list of trusted public keys:

```
ssh-keygen -Y verify -f ./allowed_signers -I johndoe@example.org -n test -s message.sig  < message
```

# Git signing

SSH signatures can also be used with Git: Both commits and tags can be signed.

- Instead of using `.git`, use a separate git directory to prevent conflicts with this script's own git repository.

```
export GIT_DIR=dotgit
```

Also, set these environment variables to not interfere with your current Git settings:
```
export GIT_CONFIG_GLOBAL=
export GIT_CONFIG_SYSTEM=
```

- Check that you have an empty config now:

```
git config -l
```

- Initialize a new Git repository with default branch `main`:

```
git -c init.defaultBranch=main init
```

- Make sure this is not a bare repository:

```
git config core.bare false
```

- Before committing, configure a user name and email:

```
git config user.name 'John Doe'
git config user.email johndoe@example.org
```

- Now, add a dummy file:
```
touch README
git add README
```

- Commit:

```
git commit -m 'unsigned commit' README
```

- Check the commit log:

```
git log --oneline
```

As of now, commits are still unsigned. Let's fix that.

- Configure Git signing by setting a format and a signing key:

```
git config gpg.format ssh
git config user.signingkey ./id_ecdsa_sk_sign
```

- Stage a new commit:

```
echo "commits should be signed" >> README
git add README
```

- Sign your commit:

```
git commit -m 'signed commit' -S
```

- Again, check the commit log:

```
git log --show-signature
```

Note that the commit has a signature now.
Also note that the signatures are not trusted.

Optionally, show the raw commit object including the signature:

```
git cat-file -p HEAD
```

- To verify signatures, we still need to specify the public keys we trust using the `allowed_signers` file we created earlier:

```
git config gpg.ssh.allowedSignersFile ./allowed_signers
```

- Again, check the commit log:

```
git log --oneline --show-signature
```

We can also sign all commits by default:

```
git config commit.gpgsign true
echo 'all commits should be signed' >> README
git commit -m 'automatically signed commit' README
git log --oneline --show-signature
```

Note that we no longer needed to use the `-S` option to sign the commit.

# GitHub

Git signatures are also recognized by GitHub and GitLab.

- View your signing public key:

```
cat ./id_ecdsa_sk_sign.pub
```

- Register this public key at GitHub (https://github.com/settings/keys). Click "New SSH key", set the type to **Signing Key**, and paste the full public key line.

Once registered, any commits signed with this key and pushed to GitHub will show a "Verified" badge.

Note that:

1. All GitHub signing keys are implicitly trusted ("Verified") for commits made by that account.
2. Signing with hardware-backed keys doesn't make sense if you authenticate using passwords. Replace GitHub passwords with passkeys (https://github.com/settings/security)!

# Using a remote git server

If you have time, you can also push your signed commits to a local SSH server using Docker.

Generate a separate authentication key (best practice: don't reuse your signing key for auth):
```
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk -C 'authentication key' -N ''
```

Build and run the SSH server:
```
docker build --build-arg user=ubuntu -t ssh-server .
docker run --rm -d -p 22:22 --name ssh_demo ssh-server
```

> **Note:** The authentication key (`id_ecdsa_sk.pub`) must exist before building the Docker image, since the Dockerfile copies it into the container.

Configure a remote origin and push:
```
git remote add origin ubuntu@localhost:scratch.git

cat > sshconfig << 'EOF'
Host localhost
    IdentityFile ./id_ecdsa_sk
    StrictHostKeyChecking accept-new
EOF

export GIT_SSH_COMMAND="ssh -F ./sshconfig"
git push --set-upstream origin main
```


# Clean up

The `GIT_DIR`, `GIT_CONFIG_GLOBAL`, and `GIT_CONFIG_SYSTEM` exports are scoped to your terminal session. Close the terminal or unset them to restore your normal git config:

```
unset GIT_DIR GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM
```

Then remove the exercise files:

```
rm message{,.sig} id_ecdsa_sk_sign{,.pub} allowed_signers README
rm -rf dotgit
```

If you also did the optional remote server section:

```
docker stop ssh_demo
docker rmi ssh-server
ssh-keygen -R 'localhost'
rm id_ecdsa_sk{,.pub} sshconfig
```
