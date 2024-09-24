import argparse
import sys

from dataset_setup.data_loader import main as data_loader_main


def invoke_function1(args):
    """
    Wrapper to invoke function1 with command-line arguments.
    """
    print(f"Invoking data loader")
    data_loader_main()


def main():
    # Create an argument parser
    parser = argparse.ArgumentParser()

    # Create subparsers for different functions
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add a subparser for function1
    parser_function1 = subparsers.add_parser("data_loader", help="Invoke data loader")
    parser_function1.set_defaults(func=invoke_function1)

    # Parse the command-line arguments
    args = parser.parse_args()

    # If no command is provided, show help and exit
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Invoke the corresponding function
    args.func(args)


if __name__ == "__main__":
    main()
