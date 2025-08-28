FROM ubuntu:latest
RUN apt-get update && apt-get install -y openssh-server git
RUN mkdir /var/run/sshd
EXPOSE 22
COPY id_ecdsa.pub /home/ubuntu/.ssh/authorized_keys
USER ubuntu
RUN git init --bare -b main /home/ubuntu/scratch.git
USER root
CMD ["/usr/sbin/sshd", "-D"]
