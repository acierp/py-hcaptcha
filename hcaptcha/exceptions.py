class ChallengeError(Exception):
    pass

class RequestRejected(ChallengeError):
    pass