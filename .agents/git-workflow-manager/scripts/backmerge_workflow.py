#!/usr/bin/env python3
"""
Backmerge Workflow Script

Syncs release changes back to development branches.

Creates a backmerge/* branch from main (not from release/*) to ensure:
1. Independence: Backmerge can run anytime after main is updated
2. Completeness: Includes the merge commit on main
3. Decoupling: No dependency on release branch existing

Usage:
    podman-compose run --rm dev python .claude/skills/git-workflow-manager/scripts/backmerge_workflow.py <step>

Steps:
    pr-develop      - Create PR from backmerge branch to develop
    rebase-contrib  - Rebase contrib branch on develop
    cleanup-release - Delete release and backmerge branches
    full            - Run all steps in sequence
    status          - Show current backmerge status
"""

import argparse
import subprocess
import sys


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def get_current_branch() -> str:
    """Get current git branch name."""
    result = run_cmd(['git', 'branch', '--show-current'], check=False)
    return result.stdout.strip()


def get_contrib_branch() -> str:
    """Get the contrib branch name (contrib/<username>)."""
    result = run_cmd(['gh', 'api', 'user', '-q', '.login'], check=False)
    username = result.stdout.strip() or 'stharrold'
    return f'contrib/{username}'


def return_to_editable_branch() -> bool:
    """Return to the editable branch (contrib/*) after workflow completion."""
    contrib = get_contrib_branch()
    current = get_current_branch()

    if current == contrib:
        print(f'  Already on editable branch: {contrib}')
        return True

    print(f'\n[Return] Switching to editable branch: {contrib}')
    result = run_cmd(['git', 'checkout', contrib], check=False)

    if result.returncode != 0:
        print(f'✗ Failed to checkout {contrib}: {result.stderr}')
        return False

    print(f'✓ Now on editable branch: {contrib}')
    return True


def get_latest_version() -> str | None:
    """Get the latest version tag from main."""
    run_cmd(['git', 'fetch', 'origin', '--tags'], check=False)
    result = run_cmd(['git', 'describe', '--tags', '--abbrev=0', 'origin/main'], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def find_release_branch() -> str | None:
    """Find the most recent release branch."""
    result = run_cmd(['git', 'branch', '-r', '--list', 'origin/release/*'], check=False)
    branches = result.stdout.strip().split('\n')
    if branches and branches[0]:
        # Return the most recent (last) release branch
        return branches[-1].strip().replace('origin/', '')
    return None


def find_backmerge_branch() -> str | None:
    """Find the most recent backmerge branch."""
    result = run_cmd(['git', 'branch', '-r', '--list', 'origin/backmerge/*'], check=False)
    branches = result.stdout.strip().split('\n')
    if branches and branches[0]:
        return branches[-1].strip().replace('origin/', '')
    return None


def create_backmerge_branch(version: str) -> str | None:
    """Create backmerge branch from main.

    Args:
        version: Version string (e.g., 'v1.6.0')

    Returns:
        Branch name if successful, None otherwise.
    """
    backmerge_branch = f'backmerge/{version}'

    # Fetch latest
    run_cmd(['git', 'fetch', 'origin'], check=False)

    # Check if backmerge branch already exists
    result = run_cmd(['git', 'branch', '-r', '--list', f'origin/{backmerge_branch}'], check=False)
    if result.stdout.strip():
        print(f'  Backmerge branch {backmerge_branch} already exists')
        # Checkout existing branch
        run_cmd(['git', 'checkout', backmerge_branch], check=False)
        return backmerge_branch

    # Create branch from main
    print(f'\n[Branch] Creating {backmerge_branch} from origin/main...')
    result = run_cmd(
        ['git', 'checkout', '-b', backmerge_branch, 'origin/main'],
        check=False
    )
    if result.returncode != 0:
        print(f'✗ Failed to create {backmerge_branch}: {result.stderr}')
        return None

    # Push branch
    print(f'\n[Push] Pushing {backmerge_branch}...')
    result = run_cmd(
        ['git', 'push', '-u', 'origin', backmerge_branch],
        check=False
    )
    if result.returncode != 0:
        print(f'✗ Failed to push {backmerge_branch}: {result.stderr}')
        return None

    return backmerge_branch


def step_pr_develop(version: str = None) -> bool:
    """Create PR from backmerge branch to develop.

    Creates backmerge/<version> from main, then PRs to develop.
    This ensures the merge commit from main is included.
    """
    print('\n' + '=' * 60)
    print('STEP 1: PR Backmerge → Develop')
    print('=' * 60)

    # Determine version from latest tag if not provided
    if not version:
        version = get_latest_version()

    if not version:
        print('✗ Could not determine version. Specify --version.')
        return False

    print(f'  Backmerging version: {version}')

    # Fetch latest
    run_cmd(['git', 'fetch', 'origin'], check=False)

    # Check if develop is behind main
    result = run_cmd(
        ['git', 'rev-list', '--count', 'origin/develop..origin/main'],
        check=False
    )
    commits_behind = result.stdout.strip()

    if commits_behind == '0':
        print('⚠️  develop is already up to date with main')
        return True

    print(f'  develop is {commits_behind} commits behind main')

    # Create backmerge branch from main
    backmerge_branch = create_backmerge_branch(version)
    if not backmerge_branch:
        return_to_editable_branch()
        return False

    # Create PR
    print(f'\n[PR] Creating PR: {backmerge_branch} → develop...')
    result = run_cmd([
        'gh', 'pr', 'create',
        '--base', 'develop',
        '--head', backmerge_branch,
        '--title', f'Backmerge {version} to develop',
        '--body', (
            f'Backmerge main ({version}) to develop.\n\n'
            'Keeps develop in sync with production.\n\n'
            '🤖 Generated with [Claude Code](https://claude.com/claude-code)'
        )
    ], check=False)

    if result.returncode != 0:
        if 'already exists' in result.stderr:
            print('⚠️  PR already exists')
        else:
            print(f'✗ PR creation failed: {result.stderr}')
            return_to_editable_branch()
            return False

    # Return to editable branch
    return_to_editable_branch()

    print(f'✓ Step 1 complete: PR created {backmerge_branch} → develop')
    print('\nNext: Merge PR in GitHub, then run: backmerge_workflow.py rebase-contrib')
    return True


def step_rebase_contrib() -> bool:
    """Rebase contrib branch on develop."""
    print('\n' + '=' * 60)
    print('STEP 2: Rebase Contrib on Develop')
    print('=' * 60)

    contrib = get_contrib_branch()

    # Fetch latest
    print('\n[Fetch] Fetching latest...')
    run_cmd(['git', 'fetch', 'origin'], check=False)

    # Checkout contrib
    print(f'\n[Checkout] Switching to {contrib}...')
    result = run_cmd(['git', 'checkout', contrib], check=False)
    if result.returncode != 0:
        print(f'✗ Failed to checkout {contrib}: {result.stderr}')
        return False

    # Check for uncommitted changes
    result = run_cmd(['git', 'status', '--porcelain'], check=False)
    if result.stdout.strip():
        print('✗ Uncommitted changes detected. Commit or stash before rebase.')
        return False

    # Rebase on develop
    print(f'\n[Rebase] Rebasing {contrib} onto origin/develop...')
    result = run_cmd(['git', 'rebase', 'origin/develop'], check=False)

    if result.returncode != 0:
        print('⚠️  Rebase conflict detected!')
        print('  Resolve conflicts manually, then run:')
        print('    git rebase --continue')
        print('    git push --force-with-lease')
        return False

    # Force push with lease
    print(f'\n[Push] Force pushing {contrib}...')
    result = run_cmd(['git', 'push', '--force-with-lease', 'origin', contrib], check=False)

    if result.returncode != 0:
        print(f'✗ Push failed: {result.stderr}')
        return False

    print(f'✓ Step 2 complete: {contrib} rebased on develop')
    return True


def step_cleanup_release(version: str = None) -> bool:
    """Delete release and backmerge branches locally and remotely."""
    print('\n' + '=' * 60)
    print('STEP 3: Cleanup Branches')
    print('=' * 60)

    # Determine version
    if not version:
        version = get_latest_version()

    if not version:
        print('⚠️  No version found, skipping cleanup')
        return True

    # Make sure we're not on a branch we're about to delete
    return_to_editable_branch()

    # Cleanup release branch
    release_branch = f'release/{version}'
    print(f'\n[Delete] Cleaning up {release_branch}...')
    run_cmd(['git', 'branch', '-D', release_branch], check=False)
    result = run_cmd(['git', 'push', 'origin', '--delete', release_branch], check=False)
    if result.returncode != 0:
        if 'remote ref does not exist' in result.stderr:
            print('  Release branch already deleted or never existed')
        else:
            print(f'⚠️  Release branch delete warning: {result.stderr}')

    # Cleanup backmerge branch
    backmerge_branch = f'backmerge/{version}'
    print(f'\n[Delete] Cleaning up {backmerge_branch}...')
    run_cmd(['git', 'branch', '-D', backmerge_branch], check=False)
    result = run_cmd(['git', 'push', 'origin', '--delete', backmerge_branch], check=False)
    if result.returncode != 0:
        if 'remote ref does not exist' in result.stderr:
            print('  Backmerge branch already deleted or never existed')
        else:
            print(f'⚠️  Backmerge branch delete warning: {result.stderr}')

    print('✓ Step 3 complete: Branches cleaned up')
    return True


def show_status() -> None:
    """Show current backmerge status."""
    print('\n' + '=' * 60)
    print('BACKMERGE STATUS')
    print('=' * 60)

    current = get_current_branch()
    contrib = get_contrib_branch()

    print(f'\nCurrent branch: {current}')
    print(f'Contrib branch: {contrib}')

    # Show latest version
    version = get_latest_version()
    if version:
        print(f'Latest version: {version}')
    else:
        print('Latest version: None')

    # Show release/backmerge branches
    release_branch = find_release_branch()
    backmerge_branch = find_backmerge_branch()
    if release_branch:
        print(f'Release branch: {release_branch}')
    if backmerge_branch:
        print(f'Backmerge branch: {backmerge_branch}')

    # Check if develop is behind main
    run_cmd(['git', 'fetch', 'origin'], check=False)
    result = run_cmd(['git', 'rev-list', '--count', 'origin/develop..origin/main'], check=False)
    behind_main = result.stdout.strip()
    if behind_main and behind_main != '0':
        print(f'\n⚠️  develop is {behind_main} commits behind main')

    # Check if contrib is behind develop
    result = run_cmd(['git', 'rev-list', '--count', f'{contrib}..origin/develop'], check=False)
    behind_develop = result.stdout.strip()
    if behind_develop and behind_develop != '0':
        print(f'⚠️  {contrib} is {behind_develop} commits behind develop')

    # Determine next step
    print('\n' + '-' * 40)
    if behind_main and behind_main != '0':
        print('Next step: backmerge_workflow.py pr-develop')
    elif behind_develop and behind_develop != '0':
        print('Next step: backmerge_workflow.py rebase-contrib')
    elif release_branch or backmerge_branch:
        print('Next step: backmerge_workflow.py cleanup-release')
    else:
        print('Status: All synced, ready for next feature')


def run_full_workflow(version: str = None) -> bool:
    """Run all workflow steps in sequence."""
    print('\n' + '=' * 60)
    print('FULL BACKMERGE WORKFLOW')
    print('=' * 60)

    # Note: pr-develop requires manual PR merge, so we split the workflow
    print('\n⚠️  Full workflow requires manual PR merge between steps.')
    print('Running pr-develop first...')

    if not step_pr_develop(version):
        return_to_editable_branch()
        return False

    print('\n' + '-' * 40)
    print('MANUAL STEP: Merge the PR in GitHub')
    print('Then run: backmerge_workflow.py rebase-contrib')
    print('-' * 40)

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Backmerge Workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        'step',
        choices=['pr-develop', 'rebase-contrib', 'cleanup-release', 'full', 'status'],
        help='Workflow step to execute'
    )
    parser.add_argument(
        '--version',
        help='Version for release (e.g., v1.6.0). Auto-detected from tags if not provided.'
    )

    args = parser.parse_args()

    step_map = {
        'pr-develop': lambda: step_pr_develop(args.version),
        'rebase-contrib': step_rebase_contrib,
        'cleanup-release': lambda: step_cleanup_release(args.version),
        'full': lambda: run_full_workflow(args.version),
        'status': show_status,
    }

    success = step_map[args.step]()

    if args.step != 'status':
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
