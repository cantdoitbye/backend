from enum import Enum
class OtpPurposeEnum(Enum):
    FORGET_PASSWORD = "forget_password"
    EMAIL_VERIFICATION = "email_verification"
    OTHER = "other"