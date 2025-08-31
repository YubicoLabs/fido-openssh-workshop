FROM ubuntu:latest
RUN apt-get update && apt-get install -y openssh-server
RUN mkdir /var/run/sshd
RUN echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
RUN echo "TrustedUserCAKeys /etc/ssh/user_ca.pub" >> /etc/ssh/sshd_config
COPY id_userca.pub /etc/ssh/user_ca.pub
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
