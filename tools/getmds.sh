#!/bin/bash

echo checking jq:
command -v jq || { echo "install jq first (https://jqlang.org/download/)"; exit 127; }
echo checking step:
command -v step || { echo "install step first (https://smallstep.com/docs/step-cli/installation/)"; exit 127; }

# Retrieve fido metadata if missing
if ! test -f mds.jwt; then
    curl -Ls https://mds3.fidoalliance.org/ --output mds.jwt -z mds.jwt
    cat mds.jwt | step crypto jwt inspect --insecure | jq -r '.header.x5c[1:][]' | while read pem; do echo $pem | base64 -d | openssl x509 -inform der; done > intermediates.pem
    cat mds.jwt | step crypto jwt inspect --insecure | jq -r '.header.x5c[0]' | base64 -d | openssl x509 -inform der -out mds.pem 
    openssl verify -CApath /etc/ssl/certs -untrusted intermediates.pem mds.pem
    cat mds.jwt | step crypto jwt verify --key mds.pem --alg RS256 --subtle > mds.jwt.json
    cat mds.jwt.json | jq .payload > md.json
fi

# list all entries with an AAGUID
jq -r '.entries[] | select(.aaguid) | .metadataStatement.description' md.json 
