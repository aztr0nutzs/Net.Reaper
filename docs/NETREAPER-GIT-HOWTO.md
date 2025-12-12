# NETREAPER – Git / Release / Pipeline HOWTO

This is the "future me is tired of remembering this bullshit" guide.

Use it for:
- Normal changes
- Releases (v6.x.y)
- Hotfixes (like the sudo E2BIG bug)
- PRs via `gh`
- Tagging and publishing releases
- **VERSION SYNC** (the thing that breaks tests every fucking time)
- CI/CD pipeline understanding
- SBOM and checksum generation

All commands assume:
```bash
cd ~/NETREAPER
```

---

## VERSION SYNC CHECKLIST (CRITICAL)

**Every version bump MUST update ALL of these. Tests compare them — mismatches break CI.**

| File                    | Location       | Format    | Example     |
|-------------------------|----------------|-----------|-------------|
| `VERSION`               | entire file    | `X.X.X`   | `6.2.2`     |
| `bin/netreaper`         | line 12        | `X.X.X`   | `6.2.2`     |
| `bin/netreaper`         | line 22        | `X.X.X`   | `6.2.2`     |
| `bin/netreaper-install` | line 4         | `vX.X.X`  | `v6.2.2`    |
| `bin/netreaper-install` | line 14        | `X.X.X`   | `6.2.2`     |
| `README.md`             | header section | `vX.X.X`  | `v6.2.2`    |
| `CHANGELOG.md`          | new entry      | `X.X.X`   | `## [6.2.2]`|

### Quick Version Bump Commands

```bash
# Set the new version
NEW_VERSION="6.2.3"

# Update VERSION file
echo "$NEW_VERSION" > VERSION

# Update bin/netreaper (lines 12 and 22)
sed -i "s/^# Version: .*/# Version: $NEW_VERSION/" bin/netreaper
sed -i "s/^VERSION=\".*\"/VERSION=\"$NEW_VERSION\"/" bin/netreaper

# Update bin/netreaper-install (lines 4 and 14)
sed -i "s/^# Version: .*/# Version: v$NEW_VERSION/" bin/netreaper-install
sed -i "s/^VERSION=\".*\"/VERSION=\"$NEW_VERSION\"/" bin/netreaper-install

# Verify all match
echo "VERSION file: $(cat VERSION)"
grep -n "Version:" bin/netreaper bin/netreaper-install
grep -n "^VERSION=" bin/netreaper bin/netreaper-install
```

### Verify Before Commit

```bash
# Run version test
NR_NON_INTERACTIVE=1 bats tests/*.bats

# Specifically check version test
bats tests/*.bats --filter "version"
```

---

## Release Pipeline Overview

### Big Picture

**Goal:** One consistent flow:

1. You merge code to `main`
2. You decide the next version (`vX.Y.Z`)
3. You create a tag (or use a workflow to bump + tag)
4. CI:
   - Runs tests
   - Generates/updates changelog
   - Builds assets
   - Generates SBOM
   - Generates checksums
   - Creates a GitHub Release
   - Attaches assets
   - Marks it as stable or prerelease depending on tag

### Versioning & Tagging Strategy

**Semantic Versioning (SemVer):** `MAJOR.MINOR.PATCH` → `vX.Y.Z`

| Type | When |
|------|------|
| MAJOR | Breaking changes |
| MINOR | New features |
| PATCH | Bug fixes |

**Tag Types:**

| Type | Format | Example |
|------|--------|---------|
| Stable | `vX.Y.Z` | `v6.2.1`, `v6.3.0` |
| Alpha | `vX.Y.Z-alpha.N` | `v6.3.0-alpha.1` |
| Beta | `vX.Y.Z-beta.N` | `v6.3.0-beta.1` |
| RC | `vX.Y.Z-rc.N` | `v6.3.0-rc.1` |
| Nightly | `vX.Y.Z-nightly.YYYYMMDD` | `v6.3.0-nightly.20251210` |

Pre-release tags automatically produce prerelease GitHub releases.

### Branch Conventions

| Branch | Purpose |
|--------|---------|
| `main` | Source of truth, always releasable |
| `feature/*` | Development branches |
| `fix/*` | Bug fix branches |
| `release/vX.Y.Z` | Optional release-prep branches |

### Workflows

| Workflow | Trigger | Actions |
|----------|---------|---------|
| CI | PRs | Lint + test only |
| Release | Tag push (`v*`) | Build, changelog, SBOM, checksums, GH Release |
| Nightly | Cron or prerelease tag | Prerelease artifacts |

---

## 0. Basics / Sanity Check

### Check where you are and what's dirty

```bash
cd ~/NETREAPER
git status
```

- `On branch main` → you're on main
- `working tree clean` → no local changes

If there are modified files → commit or discard them before switching branches.

### Pull latest main

```bash
git checkout main
git pull
```

---

## 1. Normal Feature / Change Flow

**Goal:** Adding/changing something that isn't an emergency hotfix.

### Steps

1. **Make sure main is up to date**
```bash
cd ~/NETREAPER
git checkout main
git pull
```

2. **Create a feature branch**
```bash
git checkout -b feature/<short-name>
# e.g. git checkout -b feature/new-scan-mode
```

3. **Make changes, then check status**
```bash
git status
```

4. **Stage and commit**
```bash
git add <files>              # or: git add .
git commit -m "Short summary" -m "Longer explanation if needed"
```

5. **Push the branch**
```bash
git push -u origin feature/<short-name>
```

6. **Open PR to main**
```bash
gh pr create \
  --title "Short summary of change" \
  --body "Details, why, notes" \
  --base main \
  --head feature/<short-name>
```

7. **Merge the PR**
```bash
gh pr merge --squash --delete-branch
```

Now `main` has your feature, and the branch is gone.

---

## 2. Release Flow (new minor/major version)

**Example:** going from v6.2.2 → v6.3.0.

### 1. Prepare a release branch

```bash
cd ~/NETREAPER
git checkout main
git pull
git checkout -b release/v6.3.0
```

### 2. Bump the version (ALL LOCATIONS)

```bash
NEW_VERSION="6.3.0"

# VERSION file
echo "$NEW_VERSION" > VERSION

# bin/netreaper
sed -i "s/^# Version: .*/# Version: $NEW_VERSION/" bin/netreaper
sed -i "s/^VERSION=\".*\"/VERSION=\"$NEW_VERSION\"/" bin/netreaper

# bin/netreaper-install
sed -i "s/^# Version: .*/# Version: v$NEW_VERSION/" bin/netreaper-install
sed -i "s/^VERSION=\".*\"/VERSION=\"$NEW_VERSION\"/" bin/netreaper-install
```

### 3. Update docs / README / CHANGELOG

Update README.md header to match new version.

Add new entry at top of CHANGELOG.md:

```markdown
## [6.3.0] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

Add link at bottom:
```markdown
[6.3.0]: https://github.com/Nerds489/NETREAPER/compare/v6.2.2...v6.3.0
```

### 4. Verify and commit release prep

```bash
# Verify versions match
NR_NON_INTERACTIVE=1 bats tests/*.bats

# Commit
git add VERSION README.md CHANGELOG.md bin/netreaper bin/netreaper-install docs/
git commit -m "Release v6.3.0 — <short summary>" \
  -m "Describe the main changes (new features, breaking changes, etc.)."
```

### 5. Push branch + PR

```bash
git push -u origin release/v6.3.0

gh pr create \
  --title "Release v6.3.0" \
  --body "Prepare NETREAPER v6.3.0.

Summary:
- Bullet list of key changes
..." \
  --base main \
  --head release/v6.3.0

gh pr merge --squash --delete-branch
```

### 6. Tag and release

Once merged and main is updated:

```bash
git checkout main
git pull
git tag v6.3.0
git push origin v6.3.0
```

If you need a manual GitHub release:

```bash
gh release create v6.3.0 \
  --title "v6.3.0 — <name>" \
  --notes "Copy/paste your changelog / summary here."
```

---

## 3. Hotfix / Patch Release Flow

**Use this when:** something is broken in a released version and you need a small targeted fix.

**Example:** sudo E2BIG argument list too long.

### 1. Create a fix branch from main

```bash
cd ~/NETREAPER
git checkout main
git pull
git checkout -b fix/<short-name>
# e.g. git checkout -b fix/sudo-e2big
```

### 2. Fix the bug

- Edit the relevant file(s)
- Keep the change as small and surgical as possible
- Add a comment explaining the fix

Verify:
```bash
bash -n bin/netreaper
shellcheck bin/netreaper
```

And manually run the command that was broken.

### 3. Commit the fix

```bash
git add bin/netreaper
git commit -m "Fix E2BIG 'argument list too long' in sudo call" \
  -m "Resolve user-reported error in NETREAPER v6.2.1 where sudo failed with \
'argument list too long' due to massive argument expansion. Stream input into \
sudo instead of inlining huge arguments to avoid ARG_MAX. Verified with \
bash -n, shellcheck, and manual test."
```

### 4. Push branch and PR

```bash
git push -u origin fix/<short-name>

gh pr create \
  --title "Fix sudo E2BIG 'argument list too long' error" \
  --body "Bug fix description, root cause, fix, verification steps." \
  --base main \
  --head fix/<short-name>
```

### 5. Merge the PR

```bash
# You can't approve your own PR, so just merge:
gh pr merge --squash --delete-branch
```

### 6. Cut a patch release (e.g. v6.2.2)

**Bump VERSION in ALL locations:**

```bash
git checkout main
git pull

NEW_VERSION="6.2.2"

echo "$NEW_VERSION" > VERSION
sed -i "s/^# Version: .*/# Version: $NEW_VERSION/" bin/netreaper
sed -i "s/^VERSION=\".*\"/VERSION=\"$NEW_VERSION\"/" bin/netreaper
sed -i "s/^# Version: .*/# Version: v$NEW_VERSION/" bin/netreaper-install
sed -i "s/^VERSION=\".*\"/VERSION=\"$NEW_VERSION\"/" bin/netreaper-install
```

Add entry to CHANGELOG.md:

```markdown
## [6.2.2] - YYYY-MM-DD

### Fixed
- Fix sudo E2BIG 'argument list too long' error by streaming input into sudo
  instead of passing massive argument lists.
```

And link at bottom:
```markdown
[6.2.2]: https://github.com/Nerds489/NETREAPER/compare/v6.2.1...v6.2.2
```

**Verify, commit, tag:**

```bash
# VERIFY FIRST
NR_NON_INTERACTIVE=1 bats tests/*.bats

# Commit + tag
git add VERSION CHANGELOG.md README.md bin/netreaper bin/netreaper-install
git commit -m "Release v6.2.2 — sudo E2BIG fix"
git tag v6.2.2
git push origin main
git push origin v6.2.2
```

Create GH release:

```bash
gh release create v6.2.2 \
  --title "6.2.2 — sudo E2BIG fix" \
  --notes "Fix sudo E2BIG 'argument list too long' error in NETREAPER v6.2.1."
```

---

## 4. Pre-Release Channels

### Tag Formats

```
vX.Y.Z-alpha.N
vX.Y.Z-beta.N
vX.Y.Z-rc.N
vX.Y.Z-nightly.YYYYMMDD
```

### Creating a Pre-Release

```bash
git tag v6.3.0-alpha.1
git push origin v6.3.0-alpha.1

gh release create v6.3.0-alpha.1 \
  --title "v6.3.0-alpha.1" \
  --notes "Alpha release for testing new features." \
  --prerelease
```

Workflow detects suffix → marks GH release as prerelease automatically.

---

## 5. Release Asset Bundling

### What to Package

| Asset | Description |
|-------|-------------|
| `netreaper` | Main CLI wrapper |
| `netreaper-install` | Installer wrapper |
| `bin/` | Core executables |
| `completions/` | Shell completions |
| `docs/` | Documentation |
| `VERSION` | Version file |
| `LICENSE` | Apache 2.0 |
| `README.md` | Main readme |

### Build Step Example

```bash
TAG=$(cat VERSION)
tar czf dist/netreaper-${TAG}-source.tar.gz \
  bin/ netreaper netreaper-install docs/ completions/ VERSION README.md LICENSE
```

Attach via `softprops/action-gh-release` in CI.

---

## 6. SBOM & SHA256 Checksums

### Generate SBOM (Software Bill of Materials)

Using **syft**:

```bash
syft dir:. -o spdx-json > dist/netreaper-${TAG}-sbom.spdx.json
```

### Generate SHA256 Checksums

```bash
cd dist
for f in *; do sha256sum "$f" > "$f.sha256"; done
```

Or single file:

```bash
sha256sum dist/netreaper-${TAG}-source.tar.gz > dist/netreaper-${TAG}-source.tar.gz.sha256
```

Attach all `.sha256` files to release.

---

## 7. Using `gh` Without Screwing Yourself

### Create PR from current branch

```bash
gh pr create \
  --title "Your title" \
  --body "Your detailed explanation" \
  --base main \
  --head <current-branch-name>
```

### Merge PR (squash + delete branch)

```bash
gh pr merge --squash --delete-branch
```

**Note:** You cannot approve your own PR, so `gh pr review --approve` will fail for you. That's normal. Just run `gh pr merge` directly.

---

## 8. GitHub Actions Permission Error

### "Resource not accessible by integration"

This is GitHub Actions being stingy with permissions.

**Fix:** In the workflow file (e.g. `.github/workflows/release.yml`) make sure you have:

```yaml
permissions:
  contents: write
```

at the top level. Without that, actions like `softprops/action-gh-release` can't create or fetch releases.

---

## 9. Panic Section — "Did I Fuck It?"

### Check what branch you're on

```bash
git status
```

- On `main` but changes you didn't mean? → commit to a feature/fix branch, or `git restore` to discard
- On random branch? → `git checkout main` (after dealing with changes)

### See what's between two tags

```bash
git log --oneline v6.2.1..v6.2.2
git diff --stat v6.2.1..v6.2.2
```

### Move a wrong tag (if you ever need to)

```bash
git tag -d v6.2.2
git push origin :refs/tags/v6.2.2

# Point it at the correct commit
git tag v6.2.2
git push origin v6.2.2
```

### Undo last commit (before push)

```bash
git reset --soft HEAD~1   # keeps changes staged
git reset --hard HEAD~1   # nukes changes entirely
```

### Undo last commit (after push) — DANGEROUS

```bash
git revert HEAD           # creates new commit that undoes the last one
git push
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Check status | `git status` |
| New feature branch | `git checkout -b feature/<name>` |
| New fix branch | `git checkout -b fix/<name>` |
| Stage all | `git add .` |
| Commit | `git commit -m "msg"` |
| Push new branch | `git push -u origin <branch>` |
| Create PR | `gh pr create --title "..." --body "..."` |
| Merge PR | `gh pr merge --squash --delete-branch` |
| Tag release | `git tag vX.X.X && git push origin vX.X.X` |
| Create GH release | `gh release create vX.X.X --title "..." --notes "..."` |
| Create prerelease | `gh release create vX.X.X-alpha.1 --prerelease` |
| Run tests | `NR_NON_INTERACTIVE=1 bats tests/*.bats` |
| Syntax check | `bash -n bin/netreaper` |
| Lint | `shellcheck bin/netreaper` |
| Generate SBOM | `syft dir:. -o spdx-json > sbom.json` |
| Generate checksum | `sha256sum file > file.sha256` |

---

## Cheat Sheet — Release Types

### Patch release
```bash
NEW_VERSION="6.2.2"
# bump all files, commit, tag
git tag v6.2.2
git push origin v6.2.2
```

### Minor release
```bash
NEW_VERSION="6.3.0"
# bump all files, commit, tag
git tag v6.3.0
git push origin v6.3.0
```

### Major release
```bash
NEW_VERSION="7.0.0"
# bump all files, commit, tag
git tag v7.0.0
git push origin v7.0.0
```

### Pre-release
```bash
git tag v6.3.0-alpha.1
git push origin v6.3.0-alpha.1
gh release create v6.3.0-alpha.1 --prerelease --notes "Testing"
```

### Nightly (automated via workflow)
```
v6.3.0-nightly.YYYYMMDD
```

---

## The Golden Rule

**Before any commit that touches version:**

```bash
# Check all versions match
cat VERSION
grep "^VERSION=" bin/netreaper bin/netreaper-install
grep -i "v6\." README.md | head -3

# Run tests
NR_NON_INTERACTIVE=1 bats tests/*.bats
```

If any of those don't match, fix them before committing. Tests will explode otherwise.

---

## Why This Matters

- Releases become predictable
- Automated reproducible builds
- No forgotten version bumps
- SBOM + checksums improve trust/security
- Professional packaging for tools and integrators

---

© 2025 Nerds489
