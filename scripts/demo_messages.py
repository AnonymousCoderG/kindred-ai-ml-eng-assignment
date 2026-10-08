"""Adds a few extra riverside messages that have no attributes yet, so the
extraction pipeline has real work to do in a demo. The seed data is not touched
(the seed script already gives every seeded message an attribute, so those would
all be skipped as 'already processed').

Run from the project root:   python -m scripts.demo_messages
Safe to run twice: a message with identical text is not inserted again.
"""

from app.db import SessionLocal
from app.models import ConversationMessage, Member

MESSAGES = [
    ("riverside-member-2", "I'm looking for a co-founder with a strong operations background for my logistics startup."),
    ("riverside-member-4", "Happy to mentor anyone getting started with angel investing, I have time on Thursdays."),
    ("riverside-member-5", "Honestly my ADHD diagnosis changed how I work, I now plan everything in a strict calendar."),
    ("riverside-member-6", "I'm into trail running and would love a Sunday morning running group."),
    ("riverside-member-3", "My therapist suggested I go to more small gatherings, so I'm hoping to do that."),
]


def main() -> None:
    db = SessionLocal()
    ids = []
    for token, body in MESSAGES:
        member = db.query(Member).filter(Member.token == token).one()
        existing = (
            db.query(ConversationMessage)
            .filter(ConversationMessage.member_id == member.id, ConversationMessage.body == body)
            .first()
        )
        if existing is None:
            existing = ConversationMessage(member_id=member.id, club_id=member.club_id, body=body)
            db.add(existing)
            db.commit()
            db.refresh(existing)
        ids.append(existing.id)
    db.close()
    print("Demo message ids:", ids)
    print('Body to send:   {"message_ids": %s}' % ids)


if __name__ == "__main__":
    main()
