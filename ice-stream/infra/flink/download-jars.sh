#!/usr/bin/env bash
# Downloads the connector jars Flink needs
set -e
cd "$(dirname "$0")"
mkdir -p jars
M=https://repo.maven.apache.org/maven2
get() { [ -f "jars/$(basename "$1")" ] && echo "have $(basename "$1")" || curl -fL -o "jars/$(basename "$1")" "$1"; }
get $M/org/apache/flink/flink-sql-connector-kafka/3.2.0-1.19/flink-sql-connector-kafka-3.2.0-1.19.jar
get $M/org/apache/iceberg/iceberg-flink-runtime-1.19/1.6.1/iceberg-flink-runtime-1.19-1.6.1.jar
get $M/org/apache/iceberg/iceberg-aws-bundle/1.6.1/iceberg-aws-bundle-1.6.1.jar
get $M/org/apache/flink/flink-shaded-hadoop-2-uber/2.8.3-10.0/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar
echo "Done."