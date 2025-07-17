# Pre-requisites

Create the external Docker network (if it doesn't exist) sharing with Flink:

```
docker network create --driver bridge flink-network
```

## Rocket telemetry data seeder

```
pip install kafka-python
python rocket_producer.py
```
