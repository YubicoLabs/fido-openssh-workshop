FROM ubuntu:24.04
RUN apt-get update && apt-get install -y openssh-server
RUN mkdir /var/run/sshd
EXPOSE 22
COPY id_userca.pub /etc/ssh/user_ca.pub
RUN echo "TrustedUserCAKeys /etc/ssh/user_ca.pub" >> /etc/ssh/sshd_config
CMD ["/usr/sbin/sshd", "-D"]
