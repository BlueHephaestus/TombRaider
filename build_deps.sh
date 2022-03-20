#!/bin/bash
echo "Installing Dependencies with Apt"
echo "Installing Compression Tools"
apt-get -y install file
apt-get -y install tar
apt-get -y install gzip 
apt-get -y install bzip2 
apt-get -y install lzip 
apt-get -y install lzop 
apt-get -y install lzma 
apt-get -y install zip unzip
apt-get -y install rar unrar
apt-get -y install lha 
apt-get -y install unace 
apt-get -y install arj 
apt-get -y install rpm 
apt-get -y install cpio 
apt-get -y install arc 
apt-get -y install nomarch 
apt-get -y install p7zip 
apt-get -y install unalz 
apt-get -y install atool # Universal archive manager that uses all these deps




#atool --extract --subdir
#http://www.nongnu.org/atool/
#read -r -p 'First deleting any old instances and any unused elastic ips aka cancel this if thats not ok. This may take a minute. (Press any key to continue)' -n1 -s && echo ' '
