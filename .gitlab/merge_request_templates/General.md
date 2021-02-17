Closes: #XXX

## Description

<!-- Add a description -->

## Checklist

<!-- Mark the following with an 'x' once satisfied -->
- [ ] MR marked as WIP until work is done
- [ ] MR directed at `develop` branch
- [ ] MR linked to issue (Closes #XXX)
- [ ] Wrote and/or updated tests
- [ ] Ran _all_ tests using `docker-compose -p panic-tests -f docker-compose-tests.yml up --build -d test-suite` to ensure no breaks 
- [ ] Ran PANIC using `docker-compose up --build -d` and ensured that no errors are outputted in the console and logs 
- [ ] Updated relevant documentation (both inline and `doc/`)
- [ ] Updated setup scripts and config files and config examples
- [ ] Updated Pipfile and Pipfile.lock to include any new required packages
- [ ] Added an entry to the `Unreleased` section in `CHANGELOG.md`
- [ ] Used IDE auto-formatting and used an 80-char hard margin 
- [ ] Re-reviewed `Files changed` in the MR explorer
- [ ] Add `R4R` label once MR is ready for review
- [ ] Tag reviewers