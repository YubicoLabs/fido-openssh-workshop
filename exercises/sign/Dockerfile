FROM ubuntu:latest
RUN apt-get update && apt-get install -y openssh-server git
RUN mkdir -p /var/run/sshd
RUN echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
EXPOSE 22
COPY --chown=ubuntu id_ecdsa_sk.pub /home/ubuntu/.ssh/authorized_keys
USER ubuntu
RUN git init --bare -b main /home/ubuntu/scratch.git
USER root
CMD ["/usr/sbin/sshd", "-D"]
