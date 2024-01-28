from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Request(_message.Message):
    __slots__ = ("player_uuid",)
    PLAYER_UUID_FIELD_NUMBER: _ClassVar[int]
    player_uuid: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, player_uuid: _Optional[_Iterable[str]] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("failures",)
    FAILURES_FIELD_NUMBER: _ClassVar[int]
    failures: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, failures: _Optional[_Iterable[str]] = ...) -> None: ...
