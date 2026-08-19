# 2.0.0rc1 acceptance status

Updated: 2026-08-20

## Passed before the versioned rebuild

| Area | Evidence |
| --- | --- |
| Source regression | 56/56 automated tests passed |
| Build isolation | Python 3.10.20 build prefix; runtime lock matches; `pip check` passed |
| Model integrity | UniMERNet tiny weights matched the frozen SHA-256 |
| Clean portable build | PyInstaller completed from the short Windows worktree |
| Frozen GUI | GUI smoke exit 0 |
| Frozen Worker | Offline ready event, nonblank single-image result, clean shutdown |
| Worker stability sample | 3/3 deterministic predictions, zero errors |
| Handwriting pipeline | Simulated pen stroke saved to PNG and accepted as current input |
| Licensing generation | 183 locked distributions plus one MathJax override represented |

Latest pre-version-rebuild measurements:

- Notice-bearing portable: 1,935,633,168 bytes, 10,257 files.
- Packaged Worker readiness: 8.882 seconds on a repeated cold process.
- Fixture inference: 0.391 seconds.
- Three-request mean: 0.376 seconds; p95: 0.388 seconds.

These measurements prove the pipeline, not broad recognition accuracy. They
will be replaced by evidence from the versioned final candidate artifacts.

## Pending

1. Rebuild portable and installer with 2.0.0rc1 Windows metadata.
2. Run 25-request stability and installed Windows integration checks.
3. Verify install, same-path upgrade, uninstall, offline use, shortcuts, and user-data preservation.
4. Freeze and score the independently labelled 2.0 acceptance set.
5. Test cross-monitor and negative-coordinate capture on suitable hardware.
6. Commit the final manifest and checksums, then wait for explicit publication authorization.
