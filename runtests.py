#!/usr/bin/env python
import argparse
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--internet",
        action="store_true",
        help="Run tests that make requests on the Internet",
    )
    args = p.parse_args()

    exclude_tags = []
    if not args.internet:
        exclude_tags.append("internet")

    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.test_settings"
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(exclude_tags=exclude_tags)
    failures = test_runner.run_tests(["historical_currencies"])
    sys.exit(bool(failures))


if __name__ == "__main__":
    main()
