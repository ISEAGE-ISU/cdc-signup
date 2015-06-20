##########
# Exceptions
##########
class DuplicateName(Exception):
    pass


class UsernameAlreadyExistsError(Exception):
    pass


class OutOfTeamNumbersError(Exception):
    pass


class TeamAlreadyExistsError(Exception):
    pass


class PasswordMismatchError(Exception):
    pass


class OnlyRemainingCaptainError(Exception):
    pass
