AUDIENCE_CHOICES = (
    ('with_team', 'Participants with a team'),
    ('no_team', 'Participants without a team'),
    ('all', 'Blue Team Participants (All)'),
    ('red_team_all', 'Red Team Members (All)'),
    ('red_team_approved', 'Red Team Members (Approved)'),
    ('green_team_all', 'Green Team Members (All)'),
    ('green_team_approved', 'Green Team Members (Approved)'),
    ('everyone', 'Everyone'),
)


def get_user_audience(user):
    audience = ['everyone']

    if not user.participant.is_redgreen:
        audience.append('all')

        if user.participant.team:
            audience.append('with_team')
        else:
            audience.append('no_team')

    if user.participant.is_red:
        audience.append('red_team_all')

        if user.participant.approved:
            audience.append('red_team_approved')

    if user.participant.is_green:
        audience.append('green_team_all')

        if user.participant.approved:
            audience.append('green_team_approved')

    return audience


def user_in_audience(user, audience):
    if user.is_superuser or user.is_staff:
        return True

    if audience == "everyone":
        return True

    if not user.participant.is_redgreen:
        if audience == "all":
            return True
        elif audience == "with_team" and user.participant.team:
            return True
        elif audience == "no_team" and not user.participant.team:
            return True

    if user.participant.is_red:
        if audience == "red_team_all":
            return True
        elif audience == "red_team_approved" and user.participant.approved:
            return True

    if user.participant.is_green:
        if audience == "green_team_all":
            return True
        elif audience == "green_team_approved" and user.participant.approve:
            return True

    return False
