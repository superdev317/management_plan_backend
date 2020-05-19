JOB_STATUS = (
    ('publish', 'publish'),
    ('unpublish', 'unpublish'),
    ('update', 'update'),
    ('cancel', 'cancel'),
)

INTERVIEW_STATUS = (
	('schedule', 'schedule'),
    ('reschedule', 'reschedule'),
    ('decline', 'decline'),
    ('accept', 'accept'),
    ('hire', 'hire'),
    ('rehire', 'rehire'),
    ('left', 'left'),
    # ('offer_accept', 'offer_accept'),
    # ('offer_reject', 'offer_reject'),
)

RESCHEDULE_INTERVIEW_STATUS = (
    ('draft', 'draft'),
    ('accept', 'accept'),
    ('reject', 'reject'),
)

APPOINTMET_LETTER_STATUS = (
    ('draft', 'draft'),
    ('accept', 'accept'),
    ('reject', 'reject'),
)

JOB_APPLICATION_STATUS = (
	('applied', 'Applied'),
    ('schedule', 'Schedule'),
    ('offered', 'Offered'),
    ('reject', 'Reject'),
    # ('int_reject', 'Int_Reject'),
    # ('offer_accept', 'Offer_Accept'),
    # ('offer_reject', 'Offer_Reject'),
)

EMPLOYEE_STATUS = (
    ('hire', 'hire'), 
    ('rehire', 'rehire'), 
    ('join', 'join'),
    ('left', 'left'),
)

APPOINTMET_LETTER_THROUGH = (
    ('job_application', 'job_application'),
    ('direct_interview', 'direct_interview'),
    ('direct_hire', 'direct_hire'),
    ('re_hire', 're_hire'),
)

