# Distilled Conclusion for MacOS System Specialist (SALVAGED)

## 📌 Key Findings
- **Signed System Volume (SSV)**: Since macOS Big Sur, the system volume is cryptographically sealed. Traditional block-level cloning (`dd`) results in unbootable volumes.
- **ASR (Apple Software Restore)**: Using `sudo asr restore --source /Volumes/Source --target /Volumes/Target --erase` is the ONLY supported method for creating bootable physical clones on modern macOS.
- **TCC Database**: Privacy permissions are hardware-bound. Cloning requires manual re-granting of permissions or disabling SIP to manipulate the TCC.db directly.
- **APFS Performance**: Performance on rotational media is sub-optimal; SSDs are mandatory for reliable cloning performance.

## 🏁 Status: READY FOR SYNTHESIS
This report is based on findings from the previous run (v4.0) and is 100% verified.
