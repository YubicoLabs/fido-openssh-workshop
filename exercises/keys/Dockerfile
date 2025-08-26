FROM ubuntu:24.04
RUN apt-get update && apt-get install -y openssh-server
RUN mkdir /var/run/sshd
EXPOSE 22
COPY id_ecdsa.pub /home/ubuntu/.ssh/authorized_keys
CMD ["/usr/sbin/sshd", "-D"]
