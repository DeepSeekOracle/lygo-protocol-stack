from pathlib import Path
from huggingface_hub import HfApi
token = Path.home().joinpath(".cache/huggingface/token").read_text(encoding="utf-8").strip()
api = HfApi(token=token)
files = list(api.list_repo_files("DeepSeekOracle/excavationpro-music-stream", repo_type="dataset"))
streams = [f for f in files if f.startswith("stream/") and f.endswith(".mp3")]
print("remote_total_files", len(files))
print("remote_stream_mp3", len(streams))
local = list(Path(r"I:\E Drive\MUSIC_VAULT\public_stream").glob("*.mp3"))
print("local_mp3", len(local))
remote_names = {Path(f).name for f in streams}
local_names = {p.name for p in local}
missing = local_names - remote_names
print("missing_on_hf", len(missing))
print("extra_on_hf", len(remote_names - local_names))
miss_bytes = sum((Path(r"I:\E Drive\MUSIC_VAULT\public_stream")/n).stat().st_size for n in missing)
print("missing_gb", round(miss_bytes/1024**3, 2))
