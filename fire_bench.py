import argparse
import os

from http_benchmark import HTTPBenchmark


def _parse_binary_from_file(file_path: str) -> bytes:
    """Parses binary data from a file."""
    with open(file_path, 'rb') as file:
        binary_data = file.read()
        return binary_data


def _main():
    """
    Parses command line arguments and runs load test. Run python fire_bench.py --help for more information.
    """
    parser = argparse.ArgumentParser(description="HTTP Benchmarking Script.")
    parser.add_argument("url", type=str, help="URL to send requests to.")
    parser.add_argument("--duration", type=int, default="10", help="Load test duration in seconds.")
    parser.add_argument("--concurrency-levels", type=int, nargs='+',
                        help="List of concurrency levels to test.")
    parser.add_argument("--request_type", type=str, default="GET", choices=["GET", "PUT", "POST", "DELETE"],
                        help="Type of HTTP request.")
    parser.add_argument("--mode", type=str, default="exponential", choices=["burst", "uniform", "exponential"],
                        help="Load generation mode. Controls the delay between each request sent by each worker or simulated user.")
    parser.add_argument("--avg-jitter", type=int, default=10,
                        help="Average jitter duration in ms. Used in 'uniform' and 'exponential' modes")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--data", type=str, help="Data for http request as string")
    group.add_argument("--data-binary", type=str, help="Data for http request in a file")

    parser.add_argument("-H", "--header", action="append",
                        help="Add a header to the request (can be used multiple times)")

    args = parser.parse_args()

    # process headers
    headers = {}
    if args.header:
        for header in args.header:
            key, value = header.split(":", 1)
            headers[key.strip()] = value.strip()

    # process data
    data = ""
    if args.request_type.upper() != "GET":
        if args.data:
            data = args.data
        elif args.data_binary:
            if not os.path.isfile(args.data_binary):
                raise argparse.ArgumentTypeError(f"The file '{args.data_binary}' does not exist.")
            data = _parse_binary_from_file(args.data_binary)

    HTTPBenchmark(args.url, args.duration, args.concurrency_levels, args.request_type, headers, data, args.mode,
                  args.avg_jitter).run()


if __name__ == "__main__":
    _main()
