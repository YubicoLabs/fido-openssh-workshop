# Signing

Generate a new signing key:

	ssh-keygen -t ecdsa-sk -f ./id_ecdsa_sk_uv -N '' -O verify-required
	ssh-keygen -f id_ed25519_sk_user -t ed25519-sk -C 'johndoe@example.org user key' -N '' -O no-touch-required

Test your key by signing a dummy message:

	echo I owe you a drink | ssh-keygen -Y sign -f ./id_ecdsa_sk_uv -n test

# Git signing

- Use a separate git directory to prevent conflicts with this script's own repo

	export GIT_DIR=dotgit
	export GIT_CONFIG_GLOBAL=
	export GIT_CONFIG_SYSTEM=

- Check that you have an empty config now:

	git config -l

Initialize a new repository:

	git -c init.defaultBranch=main init

Note that init requires a defaultBranch.

- Make sure this is not a bare repo:

	git config core.bare false

- Add a dummy file

	touch README
	git add README

- Before comitting, configure a user name and email:

	git config user.name 'John Doe'
	git config user.email johndoe@example.org

- Commit:

	git commit -m 'unsigned commit' README

- Check the commit log:

	git log --oneline

As of now, commits are unsigned, Let's fix that.

- Configure signing by setting a format and a signing key:

	git config gpg.format ssh
	git config user.signingkey ./id_ed25519_sk_user

- Stage a new commit:

	echo "commits should be signed" >> README 
	git add README

- Sign your commit:

	git commit -m 'signed commit' -S

- Again, sheck the commit log:

	git log --show-signature

Note that the commit has a signature now.
Also note that the signatures are not trusted.

- to verify signatures, we need to specify the public keys we trust:

	echo -n 'johndoe@example.org ' > allowed_signers
	cat ./id_ed25519_sk_user.pub >> allowed_signers
	git config gpg.ssh.allowedSignersFile ./allowed_signers

- Again, sheck the commit log:

	git log --oneline --show-signature

Sign all commits by default:

	git config commit.gpgsign true
	echo 'all commits should be signed' >> README
	git commit -m 'automatically signed commit' README
	git log --oneline --show-signature

# Using a remote git server

	git config -l

Configure a remote origin:

	git remote add origin ubuntu@localhost:scratch.git

	git remote -v

- Create an ssh configi file with the following contents:

	Host localhost
	    IdentityFile ./id_ecdsa
	    StrictHostKeyChecking accept-new

- Use the Dockerfile in this directory to create an SSH server with a bare git repository.

- Configure the SSH command git uses to access the git server:

	export GIT_SSH_COMMAND="ssh -F ./sshconfig"

- Push your repo to the server:

	git push --set-upstream origin main

# Final notes

Git signatures are also recognized by GitHub and GitLab.

For instance, on GitHib, you can register your signing keys here:

	https://github.com/settings/keys

Note however that

1. all GitHub keys are implicitely trusted ("Verified"!
2. Signing with hardware-backed keys doesn't make sense if you authenticate using passwords. Replace passwords with passkeys (https://github.com/settings/security)!


# Clean up

- As before, stop the docker container and remove its image.


	make realclean

clean up

	rm README allowed_signers id_ed25519_sk_user id_ed25519_sk_user.pub

	rm -rf dotgit


