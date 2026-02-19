# GitHub Release Setup (Required)

For the release workflow to publish `v0.1`, repository settings must be:

1. `Settings -> Actions -> General -> Workflow permissions -> Read and write permissions`
2. `Allow GitHub Actions to create and approve pull requests` enabled

Workflow file:
- `.github/workflows/release.yml`

Release tag policy in workflow:
- Only `v0.1` is accepted.
