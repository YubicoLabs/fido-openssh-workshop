# Signing

In this exercise we will use hardware-backed SSH keys to generate digital signatures.

Generate a new signing key:

```
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk_sign -C 'signing key' -N '' -O verify-required
```

Test your key by signing a dummy message:

```
echo I owe you a drink > message
ssh-keygen -Y sign -f ./id_ecdsa_sk_sign -n test message
```

Note that the signature is written to the file `message.sig`.
The `test` namespace is used to distinguish between different signing domains.

- to verify signatures, we first need to specify the public keys we trust in a separate file:

```
echo -n 'johndoe@example.org ' > allowed_signers
cat ./id_ecdsa_sk_sign.pub >> allowed_signers
```

So the `allowed_signers` file contains a list of SSH user IDs and their public keys.

To verify the signature, refer to the signer identity and the list of trusted public keys:

```
ssh-keygen -Y verify -f allowed_signers -I johndoe@example.org -n test -s message.sig  < message
```

# Git signing

SSH signatures can also be used with Git: Both commits and tags can be signed.

- Instead of using `.git`, use a separate git directory to prevent conflicts with this script's own git repository.

```
export GIT_DIR=dotgit
```

Also, set these environment variable to not interfere with your current Git settings:
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

- Before comitting, configure a user name and email:

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

As of now, commits are still unsigned, Let's fix that.

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

Optionally, show the signature with command

```
git cat-file HEAD -p
```

- to verify signatures, we still need to specify the public keys we trust using the `allowed_signers` file we created earlier:

```
git config gpg.ssh.allowedSignersFile ./allowed_signers
```

- Again, sheck the commit log:

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

# Using a remote git server

Currently, we do not have a remote origin configured:
```
git config -l
```

So lets build another SSH server. To access that server, we could use our signing key, but it is better to use a separate authentication key instead:
```
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk -C 'authentication key' -N ''
```

- Use the Dockerfile in this directory to create an SSH server with a bare git repository.

```
docker build --build-arg user=ubuntu -t ssh-server .
docker run --rm -d -p 22:22 --name ssh_demo ssh-server
```

Configure a remote origin:
```
git remote add origin ubuntu@localhost:scratch.git
```

Check we now have our remote origin configured:
```
git remote -v
```

- Create an `sshconfig` file with the following contents:
```
Host localhost
    IdentityFile ./id_ecdsa_sk
    StrictHostKeyChecking accept-new
```

- Configure the SSH command git uses to access the git server:

```
export GIT_SSH_COMMAND="ssh -F ./sshconfig"
```

- Push your repo to the server:

```
git push --set-upstream origin main
```

The Git push command now uses your SSH authentication key to access the remote origin.

# Final notes

Git signatures are also recognized by GitHub and GitLab.

For instance, on GitHib, you can register your signing keys here:

```
https://github.com/settings/keys
```

Note however that

1. all GitHub keys are implicitly trusted ("Verified")
2. Signing with hardware-backed keys doesn't make sense if you authenticate using passwords. Replace GitHub passwords with passkeys (https://github.com/settings/security)!


# Clean up

- As before, stop the docker container and remove its image.

```
docker stop ssh_demo
docker rmi ssh-server

ssh-keygen -R 'localhost'
rm message{,.sig} id_ecdsa_sk_sign{,.pub} ./id_ecdsa_sk{,.pub} allowed_signers
rm -rf dotgit
```
