# Let cross provide the FROM instruction
ARG CROSS_BASE_IMAGE
FROM $CROSS_BASE_IMAGE

RUN apt-get update -y 

# Install openssl requirement for `bindgen` (https://github.com/rust-lang/rust-bindgen/issues/1797)
RUN apt-get install -y libssl-dev 

# Install llvm & libclang
RUN apt-get install -y wget lsb-release  

RUN apt install -y gnupg

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y software-properties-common 

#ca-certificates software-properties-common apt-transport-https

RUN wget https://apt.llvm.org/llvm.sh && \
    chmod +x llvm.sh && \
    ./llvm.sh 12