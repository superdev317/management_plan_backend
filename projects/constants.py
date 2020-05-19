STAGE = (
    ('idea', 'idea'),
    ('startup', 'startup'),
    ('company', 'company'),
    ('funded', 'funded'),
    ('completed', 'completed'),
    ('registration', 'registration'),
)

QUESTION_IDEA_GROUPS = (
    ('express', 'Express'),
    ('develop', 'Develop'),
    ('visual', 'Visual'),
    ('target', 'Target'),
    ('plan', 'Plan'),
)
QUESTION_STARTUP_GROUPS = (
    ('operation_management', 'Operations Management'),
    ('finances_outline', 'Finances Outline'),
    ('sales_strategy', 'Sales Strategy'),
    ('marketing_plan', 'Marketing Plan'),
)
QUESTION_REGISTRATION_GROUPS = (
    ('about_business', 'About Business'),
    ('name_and_address', 'Name & Address'),
    ('owners_and_mgmt', 'Owners & Mgmt'),
    ('tax_setup', 'Tax Setup'),
    ('business_setup', 'Business Setup'),
    ('place_order', 'Place Order'),
)

LOCATOR_YES_NO_CHOICES = ((None,''), (True,'Yes'), (False, 'No'))

QUESTION_GROUPS = QUESTION_IDEA_GROUPS + QUESTION_STARTUP_GROUPS + QUESTION_REGISTRATION_GROUPS

QUESTION_IDEA_TYPES = [
    ('text', 'Text'),
    ('list', 'List'),
    ('multiselect', 'MultiSelectList'),
    ('boolean', 'Yes/No'),
    ('radio', 'Radio'),
    ('date', 'Date'),
    ('image', 'Image'),
    ('sub_questions', 'Sub Questions'),
    ('doc_drawing', 'Document Drawing'),
    ('doc_spreadsheet', 'Document Spreadsheet'),
    ('ppt', 'PPT'),
    ('ocr', 'ocr'),
    ('productcomp', 'productcomp'),
    # ('doc_text', 'Document Text'),
]

QUESTION_STARTUP_TYPES = [
    ('text', 'Text'),
    ('list', 'List'),
    ('multiselect', 'MultiSelectList'),
    ('boolean', 'Yes/No'),
    ('radio', 'Radio'),
    ('date', 'Date'),
    ('image', 'Image'),
    ('sub_questions', 'Sub Questions'),
    #('video', 'Video'),
    ('doc_drawing', 'Document Drawing'),
    ('doc_spreadsheet', 'Document Spreadsheet'),
    ('ppt', 'PPT'),
    ('swot', 'SWOT'),
    ('ocr', 'ocr'),
    ('productcomp', 'productcomp'),
    # ('doc_text', 'Document Text'),
]
QUESTION_REGISTRATION_TYPES = [
    ('text', 'Text'),
    ('list', 'List'),
    ('multiselect', 'MultiSelectList'),
    ('boolean', 'Yes/No'),
    ('radio', 'Radio'),
    ('date', 'Date'),
    ('image', 'Image'),
    ('sub_questions', 'Sub Questions'),
    ('doc_drawing', 'Document Drawing'),
    ('doc_spreadsheet', 'Document Spreadsheet'),
    ('ppt', 'PPT'),
    ('ocr', 'ocr'),
    ('productcomp', 'productcomp'),
    # ('doc_text', 'Document Text'),
    ('companysearch', 'companysearch'),
]

QUESTION_TYPES = sorted(
    list(set(list(QUESTION_IDEA_TYPES + QUESTION_STARTUP_TYPES + QUESTION_REGISTRATION_TYPES))),
    key=lambda x: x[1]
)

PROJECT_STATUS = (
    ('draft', 'draft'),
    ('published', 'published'),
)

DOCUMENT_TYPE = (
    ('document', 'document'),
    ('spreadsheet', 'spreadsheet'),
    ('drawing', 'drawing'),
    ('diagram', 'diagram'),
    ('presentation', 'presentation'),
    ('image', 'image'),
    ('sound', 'sound'),
    ('video', 'video'),
    ('ocr', 'ocr'),
)

LIST_CHOICES = [('','')]

FEATURE_VALUE_TYPE = (
    ('value', 'value'),
    ('boolean', 'boolean'),
)

TASK_ASSIGN_STATUS= (
    ('assign', 'assign'),
    ('unassign', 'unassign'),
    ('fire', 'fire'),
    ('reassign', 'reassign'),
)

DEBT_TYPE = (
    ('secured', 'Secured'),
    ('unsecured', 'Unsecured'),
)
PAYMENT_TYPES = (
    ('',''),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('yearly', 'Yearly'),
)
RETURN_IN_FORM = (
    ('',''),
    ('stock', 'Stock'),
    ('pref_Stocks', 'Pref. Stocks'),
)
NATURE_OF_DILUTION = (
    ('complete', 'Complete'),
    ('partial', 'Partial'),

)

REMIND = (
    ('',''),
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('yearly', 'Yearly'),
)
FREQUENCY = (
    ('',''),
    ('1', '1 Time'),
    ('2', '2 Time'),
    ('3', '3 Time'),
)
REMIND_ME = (
    ('',''),
    ('between_9_to_17', 'Between 09:00 - 17:00'),
    ('24_hours', '24 Hours'),
)
RATING_CHOICES = (
    (0, 0),
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
)

DAYS_OF_WEEK = (
    ('',''),
    ('1', 'Monday'),
    ('2', 'Tuesday'),
    ('3', 'Wednesday'),
    ('4', 'Thursday'),
    ('5', 'Friday'),
    ('6', 'Saturday'),
    ('7', 'Sunday'),
)
MONTHS_IN_YEAR = (
    ('',''),
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),

)
TRANSACTION_MODE = (
    ('withdrawal', 'withdrawal'), 
    ('deposite', 'deposite'), 
)

TRANSACTION_STATUS = (
    ('pending', 'pending'), 
    ('success', 'success'), 
)
