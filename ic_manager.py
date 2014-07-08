import argparse
from os import path, mkdir
import sys
import pygit2

def github_addr(candidate):
    parts = candidate.split('/')
    if len(parts) is not 2:
        raise argparse.ArgumentTypeError(
            "{cand} is not a valid github repo".format(
            cand=candidate))
    return "https://github.com/{user}/{repo}.git".format(
        user=parts[0],
        repo=parts[1])

def get_ic_branch_name(base):
    return base

def init_repo(tdir, rurl, ic_branch_name, ic_branch_base):
    tgitpath = path.join(tdir, "target.git")

    try:
        repo = pygit2.Repository(
            tgitpath)
    except:
        repo = None
    if repo is None:
        try:
            mkdir(tgitpath)
        except:
            pass
        repo = pygit2.clone_repository(
            rurl,
            tgitpath,
            remote_name='origin',
            checkout_branch=ic_branch_base,
            bare=False)

    origins = filter(
        lambda (x, _): x == 'origin',
        [(i.name, i) for i in repo.remotes])
    if len(origins) == 0:
        remote = repo.create_remote('origin', rurl)
        remote.fetch()
    else:
        (_, remote) = origins[0]
    remote.url = rurl
    remote.save()
    remote.fetch()

    base_branch = repo.lookup_branch(
        "origin/{branch}".format(
            branch=ic_branch_base),
        pygit2.GIT_BRANCH_REMOTE)
    if base_branch is None:
        print "Error: {base} does not exist on remote".format(
            base=ic_branch_base)
        sys.exit(1)
    base_ref = base_branch.resolve().get_object()

    ic_branch = repo.lookup_branch(
        ic_branch_name)
    if ic_branch is not None:
        ic_branch.target = base_branch.resolve().target
    else:
        ic_branch = repo.create_branch(ic_branch_name, base_ref)

    repo.checkout(ic_branch.name)
    repo.reset(ic_branch.target, pygit2.GIT_RESET_HARD)
    return repo, ic_branch

def main():
    parser = argparse.ArgumentParser(
        description='Integration branch manager')
    parser.add_argument(
        '--desc-repo',
        dest='desc_repo',
        action='store',
        help='github repo describing ic branch user/repo',
        type=github_addr,
        required=True)
    parser.add_argument(
        '--target-repo',
        dest='target_repo',
        action='store',
        help='github repo for which we are constructing an ic branch user/repo',
        type=github_addr,
        required=True)
    parser.add_argument(
        '--integration-base',
        dest='integration_base',
        action='store',
        help='integration branch name base',
        default='master')
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
    args = parser.parse_args()
    ic_branch = get_ic_branch_name(args.branch_name_base)
    target_repo = init_repo(
        args.working_dir,
        args.target_repo,
        ic_branch,
        args.integration_base)
    return 0
