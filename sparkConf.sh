#!/usr/bin/env bash
cat > /etc/spark/conf/metrics.properties <<EOF
*.sink.Graphite.class=org.apache.spark.metrics.sink.GraphiteSink
*.sink.Graphite.host=109.231.122.97
*.sink.Graphite.port=5002
*.sink.GraphiteSink.period=5
*.sink.GraphiteSink.unit=seconds
master.source.jvm.class=org.apache.spark.metrics.source.JvmSource
worker.source.jvm.class=org.apache.spark.metrics.source.JvmSource
driver.source.jvm.class=org.apache.spark.metrics.source.JvmSource
executor.source.jvm.class=org.apache.spark.metrics.source.JvmSource
EOF