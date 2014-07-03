import argparse

def main():
    parser = argparse.ArgumentParser(
        description='Integration branch manager')
    parser.add_argument(
        '--desc-repo',
        dest='desc_repo',
        action='store',
        help='github repo describing ic branch',
        required=True)
    parser.add_argument(
        '--target-repo',
        dest='target_repo',
        action='store',
        help='github repo for which we are constructing an ic branch',
        required=True)
    parser.add_argument(
        '--branch-name-base',
        dest='branch_name_base',
        action='store',
        help='integration branch name base',
        required=True)
    parser.add_argument(
        '--working-dir',
        dest='working_dir',
        action='store',
        help='location of working dir, must be empty',
        required=True)
    return 0
