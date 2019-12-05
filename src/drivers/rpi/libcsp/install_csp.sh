#!/usr/bin/env bash
echo "Downloading Gomspace-libcsp v1.5"
if [ ! -d "./libcsp" ]; then
    git clone https://github.com/GomSpace/libcsp.git
    cd libcsp
    git checkout release-1.5
    #mv wscript wscript.old
    cd -
    #cp wscript libcsp/wscript
fi

cd libcsp
echo "Build libcsp"
python2 ./waf configure --with-os=posix --enable-if-zmqhub --enable-if-kiss --enable-crc32 --with-rtable cidr --with-driver-usart=linux --install-csp --prefix=../ build install
cd -
