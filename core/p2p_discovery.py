# OmniSwarm P2P Discovery v0.2
# IPFS pubsub + signed heartbeat + local fallback simulation

import asyncio
import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from typing import Callable, Optional

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    HAS_CRYPTOGRAPHY = True
except ImportError:
    serialization = None
    Ed25519PrivateKey = None
    Ed25519PublicKey = None
    HAS_CRYPTOGRAPHY = False


def _canonical_json(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _decode_pubsub_payload(raw: dict) -> Optional[dict]:
    data = raw.get("data")
    if data is None:
        return None

    payload_bytes: bytes
    if isinstance(data, bytes):
        payload_bytes = data
    elif isinstance(data, str):
        try:
            payload_bytes = base64.b64decode(data)
        except Exception:
            payload_bytes = data.encode("utf-8")
    else:
        return None

    try:
        return json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return None


class Peer:
    """Represents a discovered peer node in the network."""

    def __init__(
        self,
        node_id: str,
        address: str = "local",
        public_key: Optional[str] = None,
    ):
        self.node_id = node_id
        self.address = address
        self.public_key = public_key
        self.last_seen = time.time()
        self.latency_ms: Optional[float] = None

    def ping(self):
        self.last_seen = time.time()

    def is_alive(self, timeout: float = 60.0) -> bool:
        return (time.time() - self.last_seen) < timeout

    def to_dict(self, timeout: float = 60.0) -> dict:
        return {
            "node_id": self.node_id,
            "address": self.address,
            "public_key": self.public_key,
            "last_seen": self.last_seen,
            "alive": self.is_alive(timeout=timeout),
        }


class IPFSPubSubAdapter:
    """Thin adapter around ipfshttpclient pubsub APIs."""

    def __init__(self, api_addr: str, topic: str):
        self.api_addr = api_addr
        self.topic = topic
        self.client = None

    def connect(self):
        import ipfshttpclient

        self.client = ipfshttpclient.connect(self.api_addr)
        return self.client

    def close(self):
        if self.client is None:
            return
        try:
            self.client.close()
        except Exception:
            pass
        self.client = None

    def publish(self, payload: dict):
        if self.client is None:
            raise RuntimeError("IPFS client is not connected")
        self.client.pubsub.publish(self.topic, _canonical_json(payload))

    def subscribe(self):
        if self.client is None:
            raise RuntimeError("IPFS client is not connected")
        return self.client.pubsub.subscribe(self.topic)


class P2PDiscovery:
    """Peer-to-peer discovery for OmniSwarm nodes.

    - Preferred backend: IPFS pubsub
    - Fallback backend: local in-process simulation
    - Signed heartbeat envelopes protect peer identity.
    """

    def __init__(
        self,
        node_id: str,
        topic: str = "omni-swarm-heartbeat",
        ipfs_api_addr: str = "/dns/127.0.0.1/tcp/5001/http",
        heartbeat_interval: float = 2.0,
        peer_timeout: float = 10.0,
        enable_ipfs: Optional[bool] = None,
    ):
        self.node_id = node_id
        self.topic = topic
        self.ipfs_api_addr = ipfs_api_addr
        self.heartbeat_interval = heartbeat_interval
        self.peer_timeout = peer_timeout
        if enable_ipfs is None:
            backend = os.environ.get("OMNI_P2P_BACKEND", "ipfs").lower()
            self.enable_ipfs = backend == "ipfs"
        else:
            self.enable_ipfs = enable_ipfs

        self.peers: dict[str, Peer] = {}
        self.running = False
        self._message_handlers: list[Callable] = []
        self._message_log: list[dict] = []
        self._message_count = 0
        self._signature_failures = 0
        self._ipfs_connected = False

        self.crypto_backend = "ed25519" if HAS_CRYPTOGRAPHY else "hmac-fallback"
        if HAS_CRYPTOGRAPHY:
            self._private_key = Ed25519PrivateKey.generate()
            self.public_key = self._private_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        else:
            # Dev fallback when cryptography is unavailable.
            # Not asymmetric: public key mirrors secret material.
            self._private_key = secrets.token_bytes(32)
            self.public_key = self._private_key
        self.public_key_b64 = base64.b64encode(self.public_key).decode("ascii")
        self._peer_public_keys: dict[str, str] = {self.node_id: self.public_key_b64}

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._inbox_task: Optional[asyncio.Task] = None
        self._inbox_queue: asyncio.Queue = asyncio.Queue()
        self._subscriber_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._ipfs = IPFSPubSubAdapter(api_addr=self.ipfs_api_addr, topic=self.topic)

    async def start(self):
        self.running = True
        self._loop = asyncio.get_running_loop()
        self.peers[self.node_id] = Peer(
            node_id=self.node_id,
            address="self",
            public_key=self.public_key_b64,
        )

        if self.enable_ipfs:
            await self._start_ipfs_backend()

        self._inbox_task = asyncio.create_task(self._inbox_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        await asyncio.sleep(0.1)
        print(
            f"   [P2P] Discovery active | Node: {self.node_id} | "
            f"Backend: {'ipfs' if self._ipfs_connected else 'local'}"
        )

    async def stop(self):
        self.running = False
        self._stop_event.set()

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            await asyncio.gather(self._heartbeat_task, return_exceptions=True)

        if self._inbox_task:
            self._inbox_task.cancel()
            await asyncio.gather(self._inbox_task, return_exceptions=True)

        if self._subscriber_thread and self._subscriber_thread.is_alive():
            self._ipfs.close()
            self._subscriber_thread.join(timeout=1.0)

        self._ipfs.close()
        self._ipfs_connected = False
        print(f"   [P2P] Discovery stopped | Node: {self.node_id}")

    async def _start_ipfs_backend(self):
        try:
            await asyncio.to_thread(self._ipfs.connect)
            self._ipfs_connected = True
            self._stop_event.clear()
            self._subscriber_thread = threading.Thread(
                target=self._subscription_worker,
                name=f"ipfs-sub-{self.node_id}",
                daemon=True,
            )
            self._subscriber_thread.start()
        except Exception as exc:
            self._ipfs_connected = False
            print(f"   [WARN] IPFS backend unavailable ({exc}). Falling back to local.")

    def _subscription_worker(self):
        try:
            subscription = self._ipfs.subscribe()
            for raw in subscription:
                if self._stop_event.is_set():
                    break
                envelope = _decode_pubsub_payload(raw)
                if envelope is None or self._loop is None:
                    continue
                self._loop.call_soon_threadsafe(
                    self._inbox_queue.put_nowait,
                    envelope,
                )
        except Exception:
            # Listener shutdown or network errors are tolerated in v0.2.
            pass

    async def _inbox_loop(self):
        while self.running:
            envelope = await self._inbox_queue.get()
            await self._handle_incoming_envelope(envelope, source="ipfs")

    async def _heartbeat_loop(self):
        while self.running:
            await asyncio.sleep(self.heartbeat_interval)
            envelope = self.build_signed_heartbeat()
            await self.broadcast(envelope)

    def build_signed_heartbeat(self) -> dict:
        payload = {
            "type": "heartbeat",
            "node_id": self.node_id,
            "address": "ipfs" if self._ipfs_connected else "local",
            "public_key": self.public_key_b64,
            "timestamp": round(time.time(), 6),
        }
        signature = self._sign_payload(payload)
        return {"payload": payload, "signature": signature}

    def _sign_payload(self, payload: dict) -> str:
        message = _canonical_json(payload)
        if HAS_CRYPTOGRAPHY:
            signed = self._private_key.sign(message)
        else:
            signed = hmac.new(self._private_key, message, hashlib.sha256).digest()
        return base64.b64encode(signed).decode("ascii")

    def _verify_envelope(self, envelope: dict) -> bool:
        if not isinstance(envelope, dict):
            return False

        payload = envelope.get("payload")
        signature_b64 = envelope.get("signature")
        if not isinstance(payload, dict) or not isinstance(signature_b64, str):
            return False

        node_id = payload.get("node_id")
        if not isinstance(node_id, str):
            return False

        public_key_b64 = self._peer_public_keys.get(node_id) or payload.get("public_key")
        if not isinstance(public_key_b64, str):
            return False

        try:
            signature = base64.b64decode(signature_b64)
            message = _canonical_json(payload)
            key_bytes = base64.b64decode(public_key_b64)
            if HAS_CRYPTOGRAPHY:
                public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
                public_key.verify(signature, message)
            else:
                expected = hmac.new(key_bytes, message, hashlib.sha256).digest()
                if not hmac.compare_digest(signature, expected):
                    return False
        except Exception:
            return False

        self._peer_public_keys[node_id] = public_key_b64
        return True

    async def _handle_incoming_envelope(self, envelope: dict, source: str):
        if not self._verify_envelope(envelope):
            self._signature_failures += 1
            return

        payload = envelope["payload"]
        peer_id = payload.get("node_id")
        if peer_id == self.node_id:
            return

        self.register_peer(
            node_id=peer_id,
            address=payload.get("address", source),
            public_key=payload.get("public_key"),
        )
        self._message_count += 1

        entry = {
            "from": peer_id,
            "message": payload,
            "timestamp": payload.get("timestamp", time.time()),
            "recipients": [self.node_id],
            "signature_valid": True,
            "source": source,
        }
        self._message_log.append(entry)

        for handler in self._message_handlers:
            try:
                handler(entry)
            except Exception as exc:
                print(f"   [WARN] Handler error: {exc}")

    def register_peer(
        self,
        node_id: str,
        address: str = "local",
        public_key: Optional[str] = None,
    ) -> Peer:
        if node_id in self.peers:
            peer = self.peers[node_id]
            peer.address = address or peer.address
            if public_key:
                peer.public_key = public_key
                self._peer_public_keys[node_id] = public_key
            peer.ping()
        else:
            peer = Peer(node_id=node_id, address=address, public_key=public_key)
            self.peers[node_id] = peer
            if public_key:
                self._peer_public_keys[node_id] = public_key
            print(f"   [PEER] New peer discovered: {node_id}")
        return peer

    def remove_peer(self, node_id: str):
        if node_id in self.peers and node_id != self.node_id:
            del self.peers[node_id]
            self._peer_public_keys.pop(node_id, None)

    def get_peers(self, alive_only: bool = True) -> list[dict]:
        peers = self.peers.values()
        if alive_only:
            peers = [p for p in peers if p.is_alive(timeout=self.peer_timeout)]
        return [p.to_dict(timeout=self.peer_timeout) for p in peers]

    @property
    def peer_count(self) -> int:
        return sum(
            1
            for p in self.peers.values()
            if p.node_id != self.node_id and p.is_alive(timeout=self.peer_timeout)
        )

    async def broadcast(self, message: dict):
        entry = {
            "from": self.node_id,
            "message": message,
            "timestamp": time.time(),
            "recipients": [p.node_id for p in self.peers.values() if p.node_id != self.node_id],
        }
        self._message_log.append(entry)
        for handler in self._message_handlers:
            try:
                handler(entry)
            except Exception as exc:
                print(f"   [WARN] Handler error: {exc}")

        if self._ipfs_connected:
            try:
                await asyncio.to_thread(self._ipfs.publish, message)
                return
            except Exception as exc:
                print(f"   [WARN] IPFS publish failed ({exc}). Falling back to local.")

        # Local fallback path already emitted local handlers above.

    def on_message(self, handler: Callable):
        self._message_handlers.append(handler)

    def get_message_log(self) -> list[dict]:
        return list(self._message_log)

    def get_stats(self) -> dict:
        return {
            "node_id": self.node_id,
            "running": self.running,
            "backend": "ipfs" if self._ipfs_connected else "local",
            "total_peers": len(self.peers),
            "alive_peers": self.peer_count,
            "messages_sent": len(self._message_log),
            "messages_received": self._message_count,
            "signature_failures": self._signature_failures,
            "crypto_backend": self.crypto_backend,
        }
