import argparse

from tintinspider import controller

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'command', 
            choices=[
                    'create_project',
                ]
        )
    parser.add_argument('--name', type=str)
    parser.add_argument('--where', type=str)
    args = parser.parse_args()

    if args.command == 'create_project':
        controller.create_project(args.name, args.where)

if __name__ == '__main__':
    main()