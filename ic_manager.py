import argparse
import os
import sys
import pygit2
from os import listdir
from os.path import isfile, join

def parse_github_addr(candidate):
    parts = candidate.split('/')
    if len(parts) is not 2:
        return None
    return (parts[0], parts[1])

def format_github_addr((user, repo)):
    return "https://github.com/{user}/{repo}.git".format(
        user=user,
        repo=repo)

def github_addr(candidate):
    ret = parse_github_addr(candidate)
    if ret is None:
        raise argparse.ArgumentTypeError(
            "{cand} is not a valid github repo".format(
            cand=candidate))
    return format_github_addr(ret)

def get_ic_branch_name(base):
    return base

def desc_predicate(filename):
    return (
        len(filename) > 5 and \
        filename[-5:] == '.desc')

def desc_parse(filename):
    assert desc_predicate(filename)
    return filename[:-5]

def get_desc_files(path):
    return [(desc_parse(f), os.path.join(path, f)) \
             for f in listdir(path) if desc_predicate(f)]

def get_branches(path):
    ret = []
    with open(path) as f:
        for line in f.readlines():
            items = line.split()
            if len(items) < 2:
                continue
            cand = parse_github_addr(items[0])
            if cand is None:
                continue
            ret += [(items[1], cand)]
    return ret

def get_or_create_remote(repo, rname, rurl):
    remotes = filter(
        lambda (x, _): x == rname,
        [(i.name, i) for i in repo.remotes])
    if len(remotes) == 0:
        return repo.create_remote(rname, rurl)
    remote = remotes[0][1]
    remote.url = rurl
    remote.save()
    return remote

def l(x):
    print x
def try_merge(repo, ic_branch, remote, branch, logger=l):
    user, reponame = remote
    rname = "{user}-{repo}".format(user=user, repo=reponame)
    rhandle = get_or_create_remote(repo, rname, format_github_addr(remote))
    rhandle.fetch()

def init_repo(tdir, rurl, ic_branch_name, ic_branch_base, dir_name):
    tgitpath = os.path.join(tdir, dir_name)

    try:
        repo = pygit2.Repository(
            tgitpath)
    except:
        repo = None
    if repo is None:
        try:
            os.mkdir(tgitpath)
        except:
            pass
        repo = pygit2.clone_repository(
            rurl,
            tgitpath,
            remote_name='origin',
            checkout_branch=ic_branch_base,
            bare=False)

    remote = get_or_create_remote(repo, 'origin', rurl)
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
    return repo, ic_branch, tgitpath

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
    target_repo, ic_branch, target_repo_path = init_repo(
        args.working_dir,
        args.target_repo,
        ic_branch,
        args.integration_base,
        'target.git')
    info_repo, info_branch, info_repo_path = init_repo(
        args.working_dir,
        args.desc_repo,
        'master',
        'master',
        'desc.git')

    desc_files = get_desc_files(info_repo_path)
    desc_files = filter(lambda (x, _): x == args.branch_name_base, desc_files)
    for _, path in desc_files:
        for branch, github_remote in get_branches(path):
            try_merge(target_repo, ic_branch, github_remote, branch)
    return 0
