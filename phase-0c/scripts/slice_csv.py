#!/usr/bin/env python3
"""Create a bounded derived CSV slice without changing the staged raw export."""
import argparse
import csv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument("--start", required=True, help="YYYY.MM.DD HH:MM:SS[.fff]")
    parser.add_argument("--end", required=True, help="YYYY.MM.DD HH:MM:SS[.fff]")
    parser.add_argument("--date-column", default="Date")
    parser.add_argument("--clock-column", default="Time")
    args = parser.parse_args()
    count = 0
    with open(args.source, newline="") as source, open(args.destination, "w", newline="") as destination:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(destination, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            stamp = f"{row[args.date_column]} {row[args.clock_column]}"
            if args.start <= stamp <= args.end:
                writer.writerow(row)
                count += 1
    print(count)


if __name__ == "__main__":
    main()
