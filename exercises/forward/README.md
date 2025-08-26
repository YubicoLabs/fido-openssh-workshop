# Using ssh-agent with security keys

ssh-agent is normally used to load private keys in memory, so you don't have to enter the passphrase multiple times.
Instead, the passphrase is only required when adding the key to ssh-agent (in order to decrypt the private key).

Becasue security keys cannot export private keys, they cannot be loaded in memory be ssh-agent.
Instead, the reference (credential ID) to the private key is loaded.
This is why it doesn't make sense to use a passphrase to protect the private key file - it doesn't contain a private key.
It also means ssh-agent is not often used with security keys.

There are exceptions though:

1. When both UV and UP are not required. But that is almost never a good idea (except perhaps in some automation scenarios where it is unfeasible to perform UV/UP a large number of times).
2. When using agent-forwarding.

In this exercise we consider the second scenario.

# Agent forwarding

Agent forwarding can be dangerous if you sign in to a rogue server - the server can access the agent running on your client remotely, and use private keys stored in memory unnoticed..
When using a security key, you can prevent this by requiring user presence or even user verification.

- Open a terminal and launch ssh-agent in the foreground

```
/usr/bin/ssh-agent/ssh-agent -d
```

Note the environment variable export (`SSH_AUTH_SOCK`) printed on stdout.

- Open a second terminal and export `SSH_AUTH_SOCK`:

```
SSH_AUTH_SOCK=...; export SSH_AUTH_SOCK;
```


- Generate a new key:

```
ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk -N ""
```

- Verify you can use local signing using your private key:

```
echo hello | ssh-keygen -Y sign -f ./id_ecdsa_sk -n test
```

- Remove any keys present in ssh-agent:

```
ssh-add -D
```

- Add your key to ssh-agent:

```
ssh-add ./id_ecdsa_sk
```

- Verify it is now listed:

```
ssh-add -l
```

- Verify you can perform local signing using the agent (referring to public keys):

```
echo hello | ssh-keygen -Y sign -f ./id_ecdsa_sk.pub -n test
```

- Use the Dockerfile to launch an SSH server

- Copy the public key to the server:

```
scp ./id_ecdsa_sk.pub ubuntu@localhost:.
```

- Sign into the server using agent forwarding:

```
ssh -A ubuntu@localhost
```

- On the server, sign some data via agent forwarding:

```
echo hello | ssh-keygen -Y sign -f id_ecdsa_sk.pub -n test
```

Note that the signature requires user presence: no silent use of the private key is possible.

# Using UV

Repeat the exercise, but now also require user verification (`-O verify-required`).
The problem now is that usually, ssh-agent does not have a TTY to prompt for the PIN.
This is usually solved by a helper program such as `ssh-askpass`.

- Install a version of `ssh-askpass` on your system that allows reading PINs from a terminal

- Let ssh-agent know how to ask for a PIN:

```
export SSH_ASKPASS=ssh-askpass
```

If you do not have a $DISPLAY, you may also need to specify:

```
export SSH_ASKPASS_REQUIRE=force
```
