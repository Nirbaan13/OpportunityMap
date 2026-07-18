"""Which interest fields each activity type typically strengthens."""

ACTIVITY_RELATED_FIELDS: dict[str, list[str]] = {
    "olympiad": [
        "mathematics",
        "physics",
        "chemistry",
        "biology",
        "computer-science",
    ],
    "hackathon": ["computer-science", "ai", "engineering"],
    "research-program": ["research", "biology", "physics", "chemistry", "ai"],
    "summer-school": [
        "mathematics",
        "physics",
        "computer-science",
        "writing",
        "research",
    ],
    "science-fair": ["biology", "chemistry", "physics", "engineering", "ai"],
    "volunteering": ["social-science", "business", "writing"],
}
