import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from data.connection import db_cursor
from data.users import User


@dataclass
class Bloom:
    id: int
    sender: User
    content: str
    sent_timestamp: datetime.datetime
    original_bloom_id: int
    reblooms_count:int


def add_bloom(
    *, sender: User, content: str, original_bloom_id: Optional[int] = None
) -> Bloom:
    hashtags = [word[1:] for word in content.split(" ") if word.startswith("#")]

    now = datetime.datetime.now(tz=datetime.UTC)
    bloom_id = int(now.timestamp() * 1000000)
    print(original_bloom_id)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO blooms (id, sender_id, content, send_timestamp, original_bloom_id) VALUES (%(bloom_id)s, %(sender_id)s, %(content)s, %(timestamp)s,%(original_bloom_id)s)",
            dict(
                bloom_id=bloom_id,
                sender_id=sender.id,
                content=content,
                timestamp=datetime.datetime.now(datetime.UTC),
                original_bloom_id=original_bloom_id,
            ),
        )
        for hashtag in hashtags:
            cur.execute(
                "INSERT INTO hashtags (hashtag, bloom_id) VALUES (%(hashtag)s, %(bloom_id)s)",
                dict(hashtag=hashtag, bloom_id=bloom_id),
            )


def get_blooms_for_user(username: str, *, before: Optional[int] = None, limit: Optional[int] = None) -> List[Bloom]:
    with db_cursor() as cur:
        kwargs = {"sender_username": username}
        before_clause = "AND id < %(before_limit)s" if before else ""
        if before:
            kwargs["before_limit"] = before
        limit_clause = make_limit_clause(limit, kwargs)

        cur.execute(
            f"""
            SELECT
                blooms.id,
                users.username,
                content,
                send_timestamp,
                original_bloom_id,
                (SELECT COUNT(*) FROM blooms AS b2 WHERE b2.original_bloom_id = blooms.id) AS reblooms_count
            FROM blooms
            INNER JOIN users ON users.id = blooms.sender_id
            WHERE username = %(sender_username)s
                {before_clause}
            ORDER BY id DESC
            {limit_clause}
            """,
            kwargs,
        )

        rows = cur.fetchall()
        blooms = [
            Bloom(
                id=row[0],
                sender=row[1],
                content=row[2],
                sent_timestamp=row[3],
                original_bloom_id=row[4],
                reblooms_count=row[5],
            )
            for row in rows
        ]
    return blooms

def get_bloom(bloom_id: int) -> Optional[Bloom]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT
                blooms.id,
                users.username,
                content,
                send_timestamp,
                original_bloom_id,
                (SELECT COUNT(*) FROM blooms AS b2 WHERE b2.original_bloom_id = blooms.id) AS reblooms_count
            FROM blooms
            INNER JOIN users ON users.id = blooms.sender_id
            WHERE blooms.id = %s
            """,
            (bloom_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Bloom(
            id=row[0],
            sender=row[1],
            content=row[2],
            sent_timestamp=row[3],
            original_bloom_id=row[4],
            reblooms_count=row[5],
        )

def get_blooms_with_hashtag(hashtag_without_leading_hash: str, *, limit: int = None) -> List[Bloom]:
    kwargs = {"hashtag_without_leading_hash": hashtag_without_leading_hash}
    limit_clause = make_limit_clause(limit, kwargs)
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                blooms.id,
                users.username,
                content,
                send_timestamp,
                original_bloom_id,
                (SELECT COUNT(*) FROM blooms AS b2 WHERE b2.original_bloom_id = blooms.id) AS reblooms_count
            FROM blooms
            INNER JOIN hashtags ON blooms.id = hashtags.bloom_id
            INNER JOIN users ON blooms.sender_id = users.id
            WHERE hashtag = %(hashtag_without_leading_hash)s
            ORDER BY send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )

        rows = cur.fetchall()
        blooms = [
            Bloom(
                id=row[0],
                sender=row[1],
                content=row[2],
                sent_timestamp=row[3],
                original_bloom_id=row[4],
                reblooms_count=row[5],
            )
            for row in rows
        ]
    return blooms

def add_rebloom(*, sender: User, id: int) -> None:
    original_bloom = get_bloom(id)
    if not original_bloom:
        return None
    add_bloom(sender=sender, content=original_bloom.content, original_bloom_id=id)


def make_limit_clause(limit: Optional[int], kwargs: Dict[Any, Any]) -> str:
    if limit is not None:
        limit_clause = "LIMIT %(limit)s"
        kwargs["limit"] = limit
    else:
        limit_clause = ""
    return limit_clause
