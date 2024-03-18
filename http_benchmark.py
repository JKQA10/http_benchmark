import asyncio
import aiohttp
import logging
import time

import numpy as np
import numpy.random
import pandas as pd

from tqdm import tqdm
from tabulate import tabulate
from typing import Any, Dict, List


class HTTPBenchmark:
    def __init__(self, url: str, duration: int, concurrency_levels: List[int], request_type: str = "GET",
                 headers: dict = None, data: Any = None, mode: str = "exponential", avg_jitter: int = 10,
                 logger: logging.Logger = None):
        """
        Initializes HTTPBenchmark class.

        Args:
            url: URL to send requests to.
            duration: Duration of the test in seconds.
            concurrency_levels: A list of concurrency levels to test.
            request_type: Type of HTTP request. Defaults to "GET".
            data: Data to be sent in a request. Ignored for GET requests.
            mode: Type of load generation ("burst", "uniform", "exponential"). Defaults to "exponential"
            avg_jitter: Average jitter duration in ms. Used in "uniform" & "exponential" mode. Defaults to 10.
            logger: Logger object. Defaults to None.
        """
        self.url = url
        self.duration = duration
        self.concurrency_levels = concurrency_levels
        self.request_type = request_type.upper()
        self.headers = headers
        self.data = data
        self.mode = mode
        self.avg_jitter = avg_jitter
        if not logger:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            self.logger = logging.getLogger()
        else:
            self.logger = logger

    def run(self) -> pd.DataFrame:
        """
        Runs HTTP benchmark tests for the specified duration.

        Returns:
            load test matrix as a pandas DataFrame
        """

        async def run_tests() -> List[Dict]:
            results = []
            for concurrency in tqdm(self.concurrency_levels):
                generator = LoadGenerator(self.url, concurrency, self.duration, self.request_type,
                                          self.headers, self.data, self.mode, self.avg_jitter)
                results.append(await generator.run())
            return results

        self.logger.info("Starting load tests...")
        df = pd.DataFrame(asyncio.run(run_tests()))
        logging.info(f"\n{tabulate(df, headers='keys', tablefmt='pretty', showindex=False)}")

        return df


class LoadGenerator:
    def __init__(self, url: str, concurrency: int, duration: int, request_type: str = "GET",
                 headers: dict = None, data: Any = None, mode: str = "exponential", avg_jitter: int = 10):
        """
        Initializes LoadGenerator class.

        Args:
            url: URL to send requests to.
            concurrency: Number of concurrent requests.
            duration: Duration of the test in seconds.
            request_type: Type of HTTP request. Defaults to "GET".
            data: Data to be sent in a request. Ignored for GET requests.
            mode: Type of load generation ("burst", "uniform", "exponential"). Defaults to "exponential"
            avg_jitter: Average jitter duration in ms. Used in "uniform" & "exponential" mode. Defaults to 10.
        """
        self.url = url
        self.concurrency = concurrency
        self.duration = duration
        self.request_type = request_type.upper()
        self.headers = headers
        self.data = data
        self.mode = mode
        self.avg_jitter = float(avg_jitter / 1000)
        self.session = None

    async def _send_request(self) -> float:
        """
        Sends a single HTTP request and records the latency.

        Returns:
            latency (ms) of request if successful, -1.0 otherwise
        """
        if self.mode == "uniform":
            await asyncio.sleep(numpy.random.uniform(0, 2 * self.avg_jitter))
        elif self.mode == "exponential":
            await asyncio.sleep(numpy.random.exponential(self.avg_jitter))

        start_time = time.monotonic()
        try:
            async with self.session.request(self.request_type, self.url, data=self.data) as response:
                await response.read()
            return (time.monotonic() - start_time) * 1000
        except Exception:
            return -1.0

    async def _worker(self, end_time: float, results: List[float], errors: List[int]) -> None:
        """
        Worker for handling requests & recording latency results.
        """
        while time.time() < end_time:
            latency = await self._send_request()
            if latency >= 0:
                results.append(latency)
            else:
                errors.append(1)

    async def run(self) -> Dict:
        """
        Runs load generation for the specified duration.

        Returns:
            load test metrics as dict
        """
        start_time = time.time()
        end_time = start_time + self.duration
        results = []  # latency data
        errors = []

        async with aiohttp.ClientSession(headers=self.headers) as self.session:
            # number of workers should equal concurrency
            tasks = [asyncio.create_task(self._worker(end_time, results, errors)) for _ in range(self.concurrency)]
            await asyncio.gather(*tasks)

        successful_requests = len(results)
        error_count = len(errors)
        error_rate = (error_count / (successful_requests + error_count))
        latencies = np.array(results)

        metrics = {
            "Concurrency Level": self.concurrency,
            "Duration (s)": self.duration,
            "Successful Requests": successful_requests,
            "Total Errors": error_count,
            "Error Rate (%)": f"{error_rate:.2f}",
        }

        # Adding latency percentiles to the data dictionary if there is latency data
        percentiles = [50, 75, 95, 99]
        if len(latencies) > 0:
            for p in percentiles:
                metrics[f"p{p} Latency (ms)"] = f"{np.percentile(latencies, p):.2f}"

        return metrics


def _main():
    """
    Example load test
    """
    url = "http://example.com"
    duration = 3  # in seconds
    concurrency_levels = [5, 10, 20]
    request_type = "POST"
    headers = {"Content-Type": "application/json"}
    data = {"key1": "value1", "key2": "value2"}

    benchmark = HTTPBenchmark(url, duration, concurrency_levels, request_type, headers, data, "exponential")
    load_test_matrix_df = benchmark.run()
    # do whatever with load test matrix...


if __name__ == "__main__":
    _main()
