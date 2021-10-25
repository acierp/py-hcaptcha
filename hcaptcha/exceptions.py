class ChallengeError(Exception):
    pass

class SolveFailed(ChallengeError):
    pass

class RequestRejected(ChallengeError):
    pass