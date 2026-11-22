"""Loopback tests: ciphers, SRP maths and a full realm+world session against tests/mock_server.py."""
from __future__ import annotations

import os
import struct
import sys
import threading
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from mock_server import MockServer, SrpServer, G, N  # noqa: E402
from simplewow.crypto import ARC4  # noqa: E402
from simplewow.definitions import ChatMessageType, LogLevel  # noqa: E402
from simplewow.game import Game  # noqa: E402
from simplewow.opcodes import WorldCommand  # noqa: E402
from simplewow.packets import OutPacket  # noqa: E402
from simplewow.srp import compute_client_proof  # noqa: E402
from simplewow.ui import GameUI  # noqa: E402


class RC4Tests(unittest.TestCase):
    def test_known_vectors(self):
        self.assertEqual(ARC4(b"Key").process(b"Plaintext").hex().upper(), "BBF316E8D940AF0AD3")
        self.assertEqual(ARC4(b"Wiki").process(b"pedia").hex().upper(), "1021BF0420")


class SrpTests(unittest.TestCase):
    def test_client_matches_independent_server_many_times(self):
        # Many rounds so both signs of (B - k*g^x) and short A/B/S values get exercised.
        for _ in range(300):
            server = SrpServer("Tester", "Secret")
            client = compute_client_proof(
                "tester", "secret", server.B_bytes, bytes([G]), N.to_bytes(32, "little"), server.salt)
            result = server.verify(client.A, client.M1)
            self.assertIsNotNone(result, "server rejected the client proof")
            key, m2 = result
            self.assertEqual(key, client.K)
            self.assertEqual(m2, client.M2_expected)

    def test_wrong_password_is_rejected(self):
        server = SrpServer("Tester", "Secret")
        client = compute_client_proof("tester", "nope", server.B_bytes, bytes([G]), N.to_bytes(32, "little"), server.salt)
        self.assertIsNone(server.verify(client.A, client.M1))


class FakeUI(GameUI):
    """Headless UI: picks the first realm, then the first character, and records output."""

    def __init__(self):
        self.log_level = LogLevel.Debug
        self.chat = []
        self.lines = []
        self.got_chat = threading.Event()

    def update(self):
        time.sleep(0.02)

    def exit(self):
        pass

    def present_realm_list(self, realm_list):
        self.realms = realm_list
        self.game.connect_to(realm_list[0])

    def present_character_list(self, characters):
        self.characters = characters
        packet = OutPacket(WorldCommand.CMSG_PLAYER_LOGIN)
        packet.write_u64(characters[0].guid)
        self.game.send_packet(packet)
        self.game.world.selected_character = characters[0]

    def present_chat_message(self, message):
        self.chat.append((message.sender.type, message.sender.sender, message.message))
        self.got_chat.set()

    def log(self, message, level=LogLevel.Info):
        self.lines.append(message)

    def log_line(self, message="", level=LogLevel.Info):
        self.lines.append(message)

    def log_exception(self, message):
        raise Exception(message)

    def read_line(self):
        raise EOFError

    def read_key(self, timeout=None):
        return None


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.server = MockServer()
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def _run(self, game):
        thread = threading.Thread(target=game.start, daemon=True)
        thread.start()
        return thread

    def test_full_session(self):
        game = Game(FakeUI, "127.0.0.1", self.server.auth_port, "tester", "Secret", LogLevel.Debug)
        thread = self._run(game)
        try:
            ui = game.ui
            self.assertTrue(ui.got_chat.wait(10), f"no chat; log={ui.lines[-8:]} errors={self.server.errors}")

            # realm list + character list parsed
            self.assertEqual(ui.realms[0].name, "MockRealm")
            self.assertEqual(ui.realms[0].realm_id, 7)
            self.assertEqual([c.name for c in ui.characters], ["Testchar", "Orcchar"])
            self.assertEqual((ui.characters[0].level, ui.characters[1].race), (80, 2))

            # world auth used the realm id and upper-cased account
            self.assertEqual(self.server.last_auth_session, dict(account="TESTER", realm_id=7))

            # message from an unknown guid was queued, name-queried and then delivered
            self.assertEqual(ui.chat[0], (ChatMessageType.Say, "Alice", "Hello from the mock"))

            # outgoing chat (encrypted header, utf-8 text) reaches the server intact
            packet = OutPacket(WorldCommand.CMSG_MESSAGECHAT)
            packet.write_u32(ChatMessageType.Say)
            packet.write_u32(7)
            packet.write_cstring("héllo wörld")
            game.send_packet(packet)
            self.assertTrue(self.server.chat_received.wait(5))
            self.assertEqual(self.server.received_chat[0], (1, 7, ["héllo wörld"]))
            self.assertEqual(self.server.errors, [])
        finally:
            game.exit()
            thread.join(5)

    def test_many_sequential_sends_stay_in_cipher_sync(self):
        game = Game(FakeUI, "127.0.0.1", self.server.auth_port, "tester", "Secret", LogLevel.Info)
        thread = self._run(game)
        try:
            self.assertTrue(game.ui.got_chat.wait(10))

            def burst(tag):
                for i in range(25):
                    packet = OutPacket(WorldCommand.CMSG_MESSAGECHAT)
                    packet.write_u32(ChatMessageType.Yell)
                    packet.write_u32(1)
                    packet.write_cstring(f"{tag}-{i}")
                    game.send_packet(packet)

            threads = [threading.Thread(target=burst, args=(t,)) for t in "ab"]
            [t.start() for t in threads]
            [t.join() for t in threads]
            deadline = time.time() + 5
            while len(self.server.received_chat) < 50 and time.time() < deadline:
                time.sleep(0.02)
            self.assertEqual(len(self.server.received_chat), 50)
            self.assertEqual(self.server.errors, [])
        finally:
            game.exit()
            thread.join(5)

    def test_wrong_password_exits_cleanly(self):
        game = Game(FakeUI, "127.0.0.1", self.server.auth_port, "tester", "WRONG", LogLevel.Info)
        game.start()  # returns by itself: no retry loop
        self.assertFalse(game.running)
        self.assertTrue(any("Wrong password" in line for line in game.ui.lines), game.ui.lines)


if __name__ == "__main__":
    unittest.main(verbosity=2)
