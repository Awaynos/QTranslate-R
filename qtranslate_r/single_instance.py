"""Один экземпляр приложения и команды из командной строки."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


def default_name() -> str:
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime and Path(runtime).is_dir():
        return str(Path(runtime) / "qtranslate-r.sock")
    uid = os.getuid() if hasattr(os, "getuid") else 0
    return f"qtranslate-r-{uid}"


class SingleInstance(QObject):
    commandReceived = Signal(str)

    def __init__(self, name: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self._name = name or default_name()
        self._server = QLocalServer(self)
        self._server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self._server.newConnection.connect(self._accept)
        self._buffers: dict[QLocalSocket, bytes] = {}

    @property
    def name(self) -> str:
        return self._name

    def start(self, command: str = "show") -> bool:
        if self._send(command):
            return False
        QLocalServer.removeServer(self._name)
        self._server.listen(self._name)
        return True

    def send(self, command: str) -> bool:
        return self._send(command)

    def stop(self) -> None:
        self._server.close()
        QLocalServer.removeServer(self._name)

    def _send(self, command: str) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self._name)
        if not socket.waitForConnected(300):
            return False
        socket.write((command + "\n").encode("utf-8"))
        socket.waitForBytesWritten(300)
        socket.disconnectFromServer()
        return True

    def _accept(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            self._buffers[socket] = b""
            socket.readyRead.connect(lambda sock=socket: self._read(sock))
            socket.disconnected.connect(lambda sock=socket: self._drop(sock))

    def _read(self, socket: QLocalSocket) -> None:
        buffer = self._buffers.get(socket, b"") + bytes(socket.readAll())
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            command = line.decode("utf-8", "replace").strip()
            if command:
                self.commandReceived.emit(command)
        self._buffers[socket] = buffer[:4096]

    def _drop(self, socket: QLocalSocket) -> None:
        self._buffers.pop(socket, None)
