# Rollback

This repository keeps an explicit rollback point before the lively README redesign:

```text
rollback/readme-swiss-20260525
```

## Preview The Previous README

```bash
git show rollback/readme-swiss-20260525:README.md
git show rollback/readme-swiss-20260525:README.en.md
```

## Restore Only The README Files

```bash
git checkout rollback/readme-swiss-20260525 -- README.md README.en.md
git commit -m "Restore previous README layout"
git push origin main
```

## Restore The Whole Repository As A New Commit

If you want the full repository content to match the rollback tag while keeping Git history linear, restore from the tag and commit the result:

```bash
git restore --source rollback/readme-swiss-20260525 -- .
git commit -m "Restore repository to rollback point"
git push origin main
```
