# GitHub and Pages deployment

The only official remote is `https://github.com/marcosjm333/windows-10.git`, branch
`main`. Never force-push this branch. GitHub Pages serves the static portal from
the same repository using the `Validate and publish` workflow.

In repository Settings → Pages, select **GitHub Actions** as the source. The
deployment job requires the `github-pages` environment, `pages: write` and
`id-token: write`; its dependency must have completed validation successfully.
Account or organization policy may require the owner to enable Pages or approve
an environment deployment. Configure main branch protection with required
validation checks through GitHub settings where your plan permits it.

No deployment is considered complete until GitHub reports the Pages job as
successful and the deployed URL responds. Code push success and website deployment
success are distinct results. Initial account configuration may require manual
intervention; no token belongs in the repository.

Build output includes only static HTML, CSS, JS and approved JSON metadata.
Workflow artifacts contain this project's EFI image and validation output, never
local Windows binaries, OVMF firmware or credentials. Pull requests validate but
cannot deploy. Publish events run only on main or an authorized manual main run.
