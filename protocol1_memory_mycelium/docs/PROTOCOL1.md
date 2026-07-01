# Protocol 1: Memory Mycelium

Distributed memory via sharded fragments with hash attestation and geographic scatter labels.

## Parameters

- **12** primary fragments per object
- **2** parity shards (simplified XOR-style grouping)
- **10** minimum valid fragments to reconstruct

## API (Python reference)

```python
from lygo_p1 import MemoryMycelium

m = MemoryMycelium()
manifest = m.store(b"payload", memory_id="example")
data = m.recall("example")
```