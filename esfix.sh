#!/usr/bin/env bash

if [ ! -f "elasticsearch-2.2.0.tar.gz" ]; then
    wget https://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.2.0/elasticsearch-2.2.0.tar.gz
fi

rm -rf /opt/elasticsearc-2.2.0

tar xvf /opt/elsaticsearch-2.2.0.tar.gz

./opt/elsaticsearch-2.2.0/bin/plugin install license
./opt/elasticsearch-2.2.0/bin/plugin install marvel-agent

