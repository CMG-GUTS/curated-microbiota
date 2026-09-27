class CuratedMicrobiotaError(Exception):
    pass


class ChecksumError(CuratedMicrobiotaError):
    pass


class UnavailableError(CuratedMicrobiotaError):
    pass
