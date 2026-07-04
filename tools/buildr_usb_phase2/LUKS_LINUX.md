# Phase 2 — LUKS data partition (Linux imaging)

Windows builder stick uses `data/` on exFAT. For **production** 32GB USB:

```bash
# Example: second partition ext4 + LUKS
sudo cryptsetup luksFormat /dev/sdX2
sudo cryptsetup open /dev/sdX2 lygo_data
sudo mkfs.ext4 /dev/mapper/lygo_data
sudo mount /dev/mapper/lygo_data /mnt/lygo_data
# layout per init_data_partition.py
```

Squashfs on Linux:

```bash
mksquashfs stack_root lygo_core.sqfs -comp zstd -Xcompression-level 19
```

Verify with `veritysetup` or sidecar `lygo_core.sha256` + `lygo_core.sig` (same as Windows tar.gz path).

Δ9Φ963