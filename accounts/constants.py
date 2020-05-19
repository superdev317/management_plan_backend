ROLES = (
    ('backer', 'backer'),
    ('creator', 'creator'),
    ('employee', 'employee'),
)

QUESTION_TYPES = (
    ('text', 'Text'),
    ('checkboxes', 'MultiSelectList'),
    ('radio', 'Radio Select'),
)

GENDER = (
	('male', 'Male'),
	('female', 'Female'),
	('other', 'Other')
)

MARITAL_STATUS = (
	('single', 'Single'),
	('married', 'Married'),
	('divorced', 'Divorced')
)

JOB_ROLE = (
	('permanent', 'Permanent'),
	('contractual', 'Contractual'),
	('freelancer', 'Freelancer')
)

PROJECT_LOCATION = (
	('onsite', 'Onsite'),
	('offsite', 'Offsite'),
)

EMPLOYEE_STATUS = (
	('hire', 'hire'),
	('rehire', 'rehire'),
	('join', 'join'),
	('left', 'left'),
)

RATING_CHOICES = (
    (0, 0),
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
)

BANK_ACCOUNT_TYPE = (
	('savings', 'savings'),
	#('fixed', 'fixed'),
	('checking', 'checking'),
)
