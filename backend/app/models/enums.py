import enum


class OpportunityType(str, enum.Enum):
    OLYMPIAD = "olympiad"
    HACKATHON = "hackathon"
    RESEARCH_PROGRAM = "research_program"
    SUMMER_SCHOOL = "summer_school"
    COMPETITION = "competition"
    SCHOLARSHIP = "scholarship"
    FELLOWSHIP = "fellowship"


class NotificationType(str, enum.Enum):
    NEW_MATCH = "new_match"
    DEADLINE_REMINDER = "deadline_reminder"
    PREMIUM_RENEWAL = "premium_renewal"
