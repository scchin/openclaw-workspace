# MacOS System & Service Expert - Process Log
Date: 2026-04-19
Goal: Research 20 top-tier technical articles on MacOS system cloning, service migration, and permission handling.

## Search Strategy
- Target Keywords: MacOS system cloning, service migration, permission handling, APFS cloning, Migration Assistant pitfalls, CCC vs SuperDuper, MacOS system migration technical guide.
- Target Sources: GitHub, Reddit, StackOverflow, professional tech blogs, clawhub.ai, skillsmp.com, refoundai.com, skills.sh.

## Findings Log
- **SSV (Signed System Volume)**: Since macOS Big Sur, block-level cloning (dd) is not bootable. Only `asr` can clone the Volume Group.
- **ASR**: The native tool for bootable clones. Command: `sudo asr restore --source /Volumes/Source --target /Volumes/Target --erase`.
- **Bootable Backups**: Largely deprecated by Apple. Recovery-based restores are the recommended path.
- **TCC Database**: Permissions are hardware-bound. Migration requires re-granting or SIP disablement.
- **UID/GID Alignment**: Critical for service migration. Use `dscl` and `chown` to prevent "Permission Denied" errors.
- **APFS Performance**: Rotational disks perform significantly worse with APFS enumeration.
- **CCC/SuperDuper!**: Still useful, but limited by Apple's SSV architecture.

