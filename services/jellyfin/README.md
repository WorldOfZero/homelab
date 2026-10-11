# Jellyfin

Jellyfin runs as `app-jellyfin` behind the `tailscale-jellyfin` sidecar. It is reachable at
`https://jellyfin.comet-stork.ts.net`. Config and cache are on the Fast pool
(`/mnt/Fast/Configuration/jellyfin/`), and media is on Vault (`/mnt/Vault/Media`).

Some settings live only in Jellyfin's own config files under `/config/config/`, not in this repo.
This file records the values those settings must have, so the server can be rebuilt.

## Hardware transcoding (NVIDIA T400)

minerva has an **NVIDIA T400 4GB** (Turing, TU117). The compose file passes it to the container
(the `deploy.resources.reservations.devices` block and the `NVIDIA_*` variables). Check it with
`sudo docker exec app-jellyfin nvidia-smi`.

Set these values in **Dashboard → Playback → Transcoding**. They are stored in
`/mnt/Fast/Configuration/jellyfin/config/config/encoding.xml`.

| Setting (UI) | `encoding.xml` key | Value | Why |
|---|---|---|---|
| Hardware acceleration | `HardwareAccelerationType` | **NVIDIA NVENC** (`nvenc`) | Before [[enable-jellyfin-nvenc-transcoding]] this was `none`, so every transcode ran on the CPU |
| Enable hardware decoding for | `HardwareDecodingCodecs` | H264, HEVC, MPEG2, MPEG4, VC1, VP8, VP9 | What Turing's NVDEC decodes. **Not AV1**: Turing has no AV1 decoder |
| HEVC 10bit / VP9 10bit | `EnableDecodingColorDepth10Hevc` / `…Vp9` | on | Turing decodes 10-bit HEVC and VP9 (HDR remuxes) |
| HEVC RExt 8/10bit, HEVC RExt 12bit | `EnableDecodingColorDepth10HevcRext` / `…12HevcRext` | off | 4:2:2 and 4:4:4 content is rare, and NVDEC can't decode 4:2:2 |
| Enable enhanced NVDEC decoder | `EnableEnhancedNvdecDecoder` | on | Jellyfin's default for NVIDIA |
| Enable hardware encoding | `EnableHardwareEncoding` | on | Encode with `h264_nvenc` |
| Allow encoding in HEVC format | `AllowHevcEncoding` | off | H.264 plays on every client. Turn it on later if remote bandwidth is tight; Jellyfin falls back to H.264 for clients that can't play HEVC |
| Allow encoding in AV1 format | `AllowAv1Encoding` | off | Turing has no AV1 encoder |
| Enable tone mapping | `EnableTonemapping` | on | CUDA tone mapping turns HDR into SDR on the GPU, for clients without HDR |
| Throttle transcodes | `EnableThrottling` | on | Stops encoding once the client has enough buffer. Saves GPU and tmpfs space |
| Delete segments | `EnableSegmentDeletion` | on | Deletes segments the client has already played, so long transcodes fit in the 4 GB tmpfs (see [[verify-jellyfin-transcode-tmpfs]]) |

Leave the other values at their defaults. The T400 is a professional card, so the GeForce limit
on concurrent NVENC sessions doesn't apply. Its 4 GB of VRAM holds a few 4K tone-mapped streams
at once.

### Check that it works

1. In a web browser client, play an HEVC or 4K film. In the player settings, set the quality to
   **720p - 4 Mbps** to force a transcode.
2. On minerva, while it plays:

   ```bash
   # GPU memory and encoder/decoder use should rise. Inside the container nvidia-smi
   # can't see processes, so an empty process list is normal.
   sudo docker exec app-jellyfin nvidia-smi --query-gpu=memory.used,utilization.encoder,utilization.decoder --format=csv
   # The newest transcode log should show CUDA decode and NVENC encode
   sudo sh -c 'f=$(ls -t /mnt/Fast/Configuration/jellyfin/config/log/FFmpeg.Transcode-*.log | head -1); grep -o -E -- "-hwaccel cuda|-init_hw_device cuda[^ ]*|h264_nvenc|tonemap_cuda" "$f" | sort -u'
   ```

   Expect `-hwaccel cuda` (or `-init_hw_device cuda…`) and `h264_nvenc`, and `tonemap_cuda` for an HDR film.
   Verified on 2026-10-11 with an HDR film: about 780 MiB of GPU memory, 93% encoder and 48% decoder use.
   Encoder use is high at the start, because Jellyfin encodes ahead as fast as it can until throttling starts.
3. In Dashboard → Activity (or the playback info overlay), the stream should show "Transcoding"
   with a hardware-accelerated video codec.
