FROM ubuntu:latest
RUN apt-get update && apt-get install -y openssh-server
RUN mkdir /var/run/sshd
RUN echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
EXPOSE 22
COPY --chown=ubuntu id_ecdsa_sk.pub /home/ubuntu/.ssh/authorized_keys
CMD ["/usr/sbin/sshd", "-D"]
