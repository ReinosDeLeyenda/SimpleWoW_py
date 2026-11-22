"""A minimal 3.3.5a realm + world server used to test the client over loopback.

The server-side SRP and header handling here is written independently of the
client code (only the RC4 cipher is shared) so a mistake on one side shows up as a
failed handshake instead of cancelling out.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import socket
import struct
import threading

from simplewow.crypto import ARC4

N_HEX = "894B645E89E1535BBDAD5B8B290650530801B18EBFBF5E8FAB3C82872A3E9BB7"
N = int(N_HEX, 16)
G = 7
K = 3

# Server->client and client->server header keys, typed independently of the client module.
SERVER_ENC_KEY = bytes.fromhex("CC98AE04E897EACA12DDC09342915357")
SERVER_DEC_KEY = bytes.fromhex("C2B3723CC6AED9B5343C53EE2F4367CE")


def sha1(*parts: bytes) -> bytes:
    h = hashlib.sha1()
    for p in parts:
        h.update(p)
    return h.digest()


def le(b: bytes) -> int:
    return int.from_bytes(b, "little")


def recv_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError
        buf += chunk
    return buf


class SrpServer:
    """Server half of SRP-6 as the WoW realm server does it."""

    def __init__(self, username: str, password: str):
        self.user = username.upper()
        self.salt = os.urandom(32)
        x = le(sha1(self.salt, sha1(f"{self.user}:{password.upper()}".encode())))
        self.v = pow(G, x, N)
        self.b = le(os.urandom(19))
        self.B = (K * self.v + pow(G, self.b, N)) % N
        self.B_bytes = self.B.to_bytes(32, "little")

    def verify(self, A_bytes: bytes, M1: bytes):
        """Returns (K, M2) if the client proof is right, else None."""
        A = le(A_bytes)
        u = le(sha1(A_bytes, self.B_bytes))
        S = pow(A * pow(self.v, u, N) % N, self.b, N).to_bytes(32, "little")
        key = bytearray(40)
        key[0::2] = sha1(bytes(S[i * 2] for i in range(16)))
        key[1::2] = sha1(bytes(S[i * 2 + 1] for i in range(16)))
        key = bytes(key)
        n_bytes = N.to_bytes(32, "little")
        g_n = bytes(a ^ b for a, b in zip(sha1(n_bytes), sha1(bytes([G]))))
        expected = sha1(g_n, sha1(self.user.encode()), self.salt, A_bytes, self.B_bytes, key)
        if not hmac.compare_digest(expected, M1):
            return None
        return key, sha1(A_bytes, M1, key)


class MockServer:
    CHAR_GUID = 0x1234
    SENDER_GUID = 0xABCDEF0102  # exercises packed-guid masks with gaps

    def __init__(self, username="Tester", password="Secret"):
        self.username, self.password = username, password
        self.auth_listener = socket.socket(); self.auth_listener.bind(("127.0.0.1", 0)); self.auth_listener.listen(5)
        self.world_listener = socket.socket(); self.world_listener.bind(("127.0.0.1", 0)); self.world_listener.listen(5)
        self.auth_port = self.auth_listener.getsockname()[1]
        self.world_port = self.world_listener.getsockname()[1]
        self.session_key = None
        self.received_chat = []          # (type, language, [target], text)
        self.chat_received = threading.Event()
        self.auth_ok = threading.Event()
        self.errors = []
        self.last_auth_session = None

    def start(self):
        for target in (self._auth_loop, self._world_loop):
            threading.Thread(target=target, daemon=True).start()

    def stop(self):
        for s in (self.auth_listener, self.world_listener):
            try:
                s.close()
            except OSError:
                pass

    # -- realm server ----------------------------------------------------------------------

    def _auth_loop(self):
        try:
            while True:
                conn, _ = self.auth_listener.accept()
                threading.Thread(target=self._auth_conn, args=(conn,), daemon=True).start()
        except OSError:
            pass

    def _auth_conn(self, conn):
        try:
            assert recv_exact(conn, 1)[0] == 0x00
            _error, size = struct.unpack("<BH", recv_exact(conn, 3))
            body = recv_exact(conn, size)
            assert body[:4] == b"WoW\x00" and body[4:7] == bytes([3, 3, 5])
            assert struct.unpack_from("<H", body, 7)[0] == 12340
            assert body[9:13] == b"68x\x00" and body[13:17] == b"niW\x00" and body[17:21] == b"SUne"
            name_len = body[29]
            assert size == 30 + name_len
            name = body[30:30 + name_len].decode()
            srp = SrpServer(name, self.password if name.upper() == self.username.upper() else "wrong")
            conn.sendall(bytes([0, 0, 0]) + srp.B_bytes + bytes([1, G, 32]) + N.to_bytes(32, "little")
                         + srp.salt + os.urandom(16) + bytes([0]))

            assert recv_exact(conn, 1)[0] == 0x01
            proof = recv_exact(conn, 20 + 32 + 20 + 2)
            result = srp.verify(proof[:32], proof[32:52])
            if result is None:
                conn.sendall(bytes([1, 4, 0, 0]))
                return
            self.session_key, m2 = result
            conn.sendall(bytes([1, 0]) + m2 + struct.pack("<IIH", 0, 0, 0))
            self.auth_ok.set()

            assert recv_exact(conn, 1)[0] == 0x10
            recv_exact(conn, 4)
            realm = (bytes([0, 0, 0]) + b"MockRealm\x00" + f"127.0.0.1:{self.world_port}".encode() + b"\x00"
                     + struct.pack("<f", 0.5) + bytes([3, 1, 7]))
            payload = struct.pack("<IH", 0, 1) + realm + bytes([0x10, 0x00])
            conn.sendall(bytes([0x10]) + struct.pack("<H", len(payload)) + payload)
            conn.recv(1)
        except Exception as ex:  # noqa: BLE001
            self.errors.append(("auth", repr(ex)))
        finally:
            conn.close()

    # -- world server ----------------------------------------------------------------------

    def _world_loop(self):
        try:
            while True:
                conn, _ = self.world_listener.accept()
                threading.Thread(target=self._world_conn, args=(conn,), daemon=True).start()
        except OSError:
            pass

    def _world_conn(self, conn):
        try:
            seed = struct.unpack("<I", os.urandom(4))[0]
            payload = struct.pack("<II", 1, seed) + os.urandom(32)
            conn.sendall(struct.pack(">H", len(payload) + 2) + struct.pack("<H", 492) + payload)

            # CMSG_AUTH_SESSION arrives unencrypted
            hdr = recv_exact(conn, 6)
            size, opcode = struct.unpack(">H", hdr[:2])[0], struct.unpack("<I", hdr[2:])[0]
            assert opcode == 493
            body = recv_exact(conn, size - 4)
            pos = 0
            build, _login_id = struct.unpack_from("<II", body, pos); pos += 8
            assert build == 12340
            end = body.index(b"\x00", pos); account = body[pos:end]; pos = end + 1
            _ltype, client_seed, region, bg, realm_id = struct.unpack_from("<IIIII", body, pos); pos += 20
            pos += 8
            digest = body[pos:pos + 20]
            self.last_auth_session = dict(account=account.decode(), realm_id=realm_id)
            expected = sha1(account, struct.pack("<I", 0), struct.pack("<I", client_seed),
                            struct.pack("<I", seed), self.session_key)
            assert digest == expected, "bad auth digest"

            def stream(key):
                s = ARC4(hmac.new(key, self.session_key, hashlib.sha1).digest())
                s.process(bytes(1024))
                return s
            enc, dec = stream(SERVER_ENC_KEY), stream(SERVER_DEC_KEY)

            def send(opcode, payload=b""):
                size = len(payload) + 2
                if size > 0x7FFF:
                    header = bytes([0x80 | ((size >> 16) & 0x7F), (size >> 8) & 0xFF, size & 0xFF]) + struct.pack("<H", opcode)
                else:
                    header = struct.pack(">H", size) + struct.pack("<H", opcode)
                conn.sendall(enc.process(header) + payload)

            send(494, bytes([0x0C]) + struct.pack("<IBIB", 0, 0, 0, 2))

            while True:
                hdr = dec.process(recv_exact(conn, 6))
                size, opcode = struct.unpack(">H", hdr[:2])[0], struct.unpack("<I", hdr[2:])[0]
                body = recv_exact(conn, size - 4)
                if opcode == 55:      # enumerate characters
                    send(59, self._char_enum())
                elif opcode == 61:    # player login
                    assert struct.unpack("<Q", body)[0] in (self.CHAR_GUID, 0x99)
                    send(0x0DDD, os.urandom(40000))   # forces the 5-byte header path
                    send(150, self._chat(1, 7, self.SENDER_GUID, "Hello from the mock"))
                elif opcode == 80:    # name query
                    guid = struct.unpack("<Q", body)[0]
                    mask, packed = 0, b""
                    for i in range(8):
                        byte = (guid >> (8 * i)) & 0xFF
                        if byte:
                            mask |= 1 << i
                            packed += bytes([byte])
                    send(81, bytes([mask]) + packed + b"\x00" + b"Alice\x00" + b"\x00" + bytes([1, 0, 1, 0]))
                elif opcode == 149:   # chat message
                    kind, lang = struct.unpack_from("<II", body)
                    rest = body[8:].split(b"\x00")
                    self.received_chat.append((kind, lang, [p.decode() for p in rest[:-1]]))
                    self.chat_received.set()
                    send(150, self._chat(9 if kind == 7 else kind, lang, self.CHAR_GUID, "echo:" + rest[-2].decode()))
        except ConnectionError:
            pass
        except Exception as ex:  # noqa: BLE001
            self.errors.append(("world", repr(ex)))
        finally:
            conn.close()

    def _char_enum(self):
        item = struct.pack("<IBI", 0, 0, 0)

        def char(guid, name, race, cls, gender, level):
            return (struct.pack("<Q", guid) + name.encode() + b"\x00" + bytes([race, cls, gender]) + bytes(5)
                    + bytes([level]) + struct.pack("<II3fIII", 12, 0, 1.0, 2.0, 3.0, 0, 0, 0) + bytes([0])
                    + struct.pack("<III", 0, 0, 0) + item * 23)

        return bytes([2]) + char(self.CHAR_GUID, "Testchar", 1, 8, 0, 80) + char(0x99, "Orcchar", 2, 1, 1, 12)

    @staticmethod
    def _chat(kind, lang, guid, text):
        t = text.encode() + b"\x00"
        return (bytes([kind]) + struct.pack("<IQI", lang, guid, 0) + struct.pack("<Q", guid)
                + struct.pack("<I", len(t)) + t + bytes([0]))
