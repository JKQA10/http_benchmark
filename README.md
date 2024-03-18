# HTTP Load-testing & Benchmark Library

An implementation of an HTTP load-testing and benchmark library using `asyncio` as it is very efficient for I/O bound tasks.

## Prerequisites

### Install Dependencies
```
pip install -r requirements.txt
```

## Features & Usage
`fire_bench.py` script supports sending HTTP requests to a URL with the following options:
* `--concurrency-level` - different levels of concurrency (e.g. number of "workers" or "users" sending requests)
* `--duration` - duration to run load test in seconds (per concurrency level)
* `--request_type`- type of request [GET, PUT, POST, DELETE]
* `--header` - headers for the request (can be used multiple times)
* `--data` - data for http request as string (ignored for "GET" requests)
* `--data-binary` - file path to data for http request (ignored for "GET" requests)
* `--mode` - load generation mode ["burst", "uniform", "exponential"]. See "Load generation strategies" section below for details
* `--avg-jitter` - average jitter or delay between requests (in ms) made by each "worker". Used only for "uniform" & "exponential" modes

### Load generation strategies
NOTE: We generate a request for each "worker" or "user" which can be adjusted by configuring the concurrency level.
* `burst` - Sends as many requests as possible with minimal delay
* `uniform` - Sends requests with random delay sampled from random distribution
* `exponential` - Sends requests with random delay sampled from exponential distribution. This is the default mode as network traffic usually resembles a poisson distribution.

### Load test matrix
Running the benchmark generates a load test matrix based on concurrency with information such as:
  * Concurrency Level
  * Successful Requests
  * Error rate
  * Test Duration
  * [50%, 75%, 95%, 99%]-ile latencies

#### Sample output
```
python fire_bench.py http://example.com --duration 3 --concurrency-levels 5 10 20 --request_type POST -d '{}' -H "Content-Type: application/json" --mode exponential --avg-jitter 10   
2024-03-17 23:23:20,888 - INFO - Starting load tests...
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:21<00:00,  7.26s/it]
2024-03-17 23:23:42,671 - INFO - 
+-------------------+--------------+---------------------+--------------+----------------+------------------+------------------+------------------+------------------+
| Concurrency Level | Duration (s) | Successful Requests | Total Errors | Error Rate (%) | p50 Latency (ms) | p75 Latency (ms) | p95 Latency (ms) | p99 Latency (ms) |
+-------------------+--------------+---------------------+--------------+----------------+------------------+------------------+------------------+------------------+
|         5         |      3       |         198         |      0       |      0.00      |      28.91       |      37.03       |      223.00      |      628.55      |
|        10         |      3       |         495         |      0       |      0.00      |      41.05       |      50.58       |      71.46       |      106.82      |
|        20         |      3       |         505         |      0       |      0.00      |      75.79       |      90.23       |      149.09      |     5065.19      |
+-------------------+--------------+---------------------+--------------+----------------+------------------+------------------+------------------+------------------+
```

## Examples 
Example usage. Please run script with `--help` option or see documentation for HTTPBenchmark and LoadGenerator class for more details.

### Run as script
```
python fire_bench.py --help # help
python fire_bench.py http://example.com --duration 3 --concurrency-levels 5 10 20 --request_type POST -d '{"key": "value"}' -H "Content-Type: application/json" --mode exponential --avg-jitter 10 
```

### Python usage example
```
url = "http://example.com"
duration = 3  # in seconds
concurrency_levels = [5, 10, 20]
request_type = "POST"
headers = {"Content-Type": "application/json"}
data = {"key1": "value1", "key2": "value2"}

benchmark = HTTPBenchmark(url, duration, concurrency_levels, request_type, headers, data, "exponential")
load_test_matrix_df = benchmark.run()
# do whatever with load test matrix...
```