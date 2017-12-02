ACCOUNT_CREATED = u"""Hi there {fname} {lname},

Your ISEAGE CDC account has been successfully created!
Please use the following credentials to log in at https://signup.iseage.org/login/

Username: {username}
Password: {password}

Make sure you change your password right away.

If you do not have a team and want support staff to place you on one, log in with the above credentials and click "Looking For Team".

You will use these credentials to log in to all CDC systems, including vCenter, Setup chat, the RDP hop, and IScorE.

If you have questions, email CDC support at {support}.
"""

ACCOUNT_CREATED_RED = u"""Hi there {fname} {lname},

Your Red Team account has been successfully created!
Please use the following credentials to log in at https://signup.iseage.org/login/

Username: {username}
Password: {password}

Make sure you change your password right away.

If you have questions, email CDC support at {support}.
"""

ACCOUNT_CREATED_GREEN = u"""Hi there {fname} {lname},

Your Green Team account has been successfully created!
Please use the following credentials to log in at https://signup.iseage.org/login/

Username: {username}
Password: {password}

Make sure you change your password right away.

If you have questions, email CDC support at {support}.
"""

PASSWORD_UPDATED = u"""Hi there {fname} {lname},

Your password has been successfully updated.

If you didn't change your password, please contact CDC support at {support} immediately.
"""

PASSWORD_RESET = u"""Hi there {fname} {lname},

Your password has been reset. Here are your new credentials:

Username: {username}
Password: {password}

You should change your password right away at https://signup.iseage.org/dashboard/

If you didn't request a password reset, please contact CDC support at {support} immediately.
"""

TEAM_CREATED = u"""Hi there {fname} {lname},

Your team has been successfully created.
Your team name is: {team}
Your team number is: {number}

You can manage your team by visiting https://signup.iseage.org/dashboard/manage_team/

Your team members should create an account and submit a request to join your team.

If you have questions, email CDC support at {support}
"""

JOIN_REQUEST_APPROVED = u"""Hi there {fname} {lname},

Your request to join a team has been approved.
You have been added to Team {number}: {team}

Be sure to get in contact with your team captain(s) if you haven't already:

{captains}

If you have questions, email CDC support at {support}
"""

CAPTAIN_REQUEST_APPROVED = u"""Hi there {fname} {lname},

Your request to be promoted to captain has been approved.

Visit https://signup.iseage.org/dashboard/manage_team/ to manage your team.

If you have questions, email CDC support at {support}
"""

JOIN_REQUEST_SUBMITTED = u"""Hi there captains,

{fname} {lname} ({email}) has requested to join your team, {team}.

Visit https://signup.iseage.org/dashboard/manage_team/ to confirm or deny this request.

If you have questions, email CDC support at {support}
"""

MEMBER_JOINED = u"""Hi there captains,

{fname} {lname} ({email}) has joined your team, {team}.

Visit https://signup.iseage.org/dashboard/manage_team/ to manage your team.

If you have questions, email CDC support at {support}
"""

CAPTAIN_REQUEST_SUBMITTED = u"""Hi there captains,

{fname} {lname} ({email}) has requested to become a captain of your team, {team}.

Visit https://signup.iseage.org/dashboard/manage_team/ to confirm or deny this request.

If you have questions, email CDC support at {support}
"""

LEFT_TEAM = u"""Hi there captains,

{fname} {lname} ({email}) has left your team, {team}.

If you have questions, email CDC support at {support}
"""

STEPPED_DOWN = u"""Hi there captains,

{fname} {lname} has stepped down as a captain of your team, {team}.

If you have questions, email CDC support at {support}
"""

TEAM_DISBANDED = u"""Hi there members,

Your team, {team}, has been disbanded.

If you wish to join or create another team, please visit https://signup.iseage.org/dashboard/

If you have questions, email CDC support at {support}
"""

CERTIFICATE = u"""Hi there {fname} {lname}!

Thank you for participating in the CDC. Your certificate is attached to this email.

If you have questions, email CDC support at {support}
"""
