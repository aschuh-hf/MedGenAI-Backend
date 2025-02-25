from __init__ import db
from models import Images, Feedback, FeedbackUsers, UserGuesses
from sqlalchemy import func, case, desc, asc


def get_feedback_with_filters(image_type=None, resolved=None, sort_by=None, sort_order='asc', limit=20, offset=0):
    try:
        # Base query
        query = (
            db.session.query(
                Images.image_id,
                Images.image_path,
                Images.image_type,
                func.count(case((Feedback.resolved == False, 1))).label("unresolved_count"),
                func.max(Feedback.date_added).label("last_feedback_time"),
                Images.upload_time,
                Images.gender,
                Images.race,
                Images.age,
                Images.disease,
            )
            .outerjoin(UserGuesses, UserGuesses.image_id == Images.image_id)
            .outerjoin(FeedbackUsers, FeedbackUsers.guess_id == UserGuesses.guess_id)
            .outerjoin(Feedback, Feedback.feedback_id == FeedbackUsers.feedback_id)
            .group_by(Images.image_id, Images.image_path, Images.image_type, Images.upload_time)
        )

        # Apply filters
        if image_type and image_type != "all":
            query = query.filter(Images.image_type == image_type)

        if resolved is not None:
            if resolved:
                query = query.having(func.count(case((Feedback.resolved == False, 1))) == 0)
            else:
                query = query.having(func.count(case((Feedback.resolved == False, 1))) > 0)

        # Sorting
        valid_sort_fields = {
            'last_feedback_time': func.max(Feedback.date_added),
            'unresolved_count': func.count(case((Feedback.resolved == False, 1))),
            'upload_time': Images.upload_time,
            'image_id': Images.image_id,
        }

        if sort_by and sort_by in valid_sort_fields:
            order_func = asc if sort_order.lower() == 'asc' else desc
            query = query.order_by(order_func(valid_sort_fields[sort_by]))
        else:
            query = query.order_by(desc(func.max(Feedback.date_added)))  # Default sorting

        # Apply limit and offset for pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        results = query.all()

        # Format results
        feedback_data = [
            {
                'image_id': row.image_id,
                'image_path': row.image_path,
                'image_type': row.image_type,
                'unresolved_count': row.unresolved_count or 0,
                'last_feedback_time': row.last_feedback_time.strftime('%Y-%m-%d') if row.last_feedback_time else None,
                'upload_time': row.upload_time.strftime('%Y-%m-%d') if row.upload_time else None,
                'gender': row.gender,
                'race': row.race,
                'age': row.age,
                'disease': row.disease,
            }
            for row in results
        ]

        return feedback_data

    except Exception as e:
        print(f"Error fetching feedback: {e}")
        return []


def get_feedback_count(image_type=None, resolved=None):
    try:
        # Base query
        query = (
            db.session.query(func.count(func.distinct(Images.image_id)))
            .outerjoin(UserGuesses, UserGuesses.image_id == Images.image_id)
            .outerjoin(FeedbackUsers, FeedbackUsers.guess_id == UserGuesses.guess_id)
            .outerjoin(Feedback, Feedback.feedback_id == FeedbackUsers.feedback_id)
        )

        # Apply filters
        if image_type and image_type != "all":
            query = query.filter(Images.image_type == image_type)

        if resolved is not None:
            query = query.filter(Feedback.resolved == resolved)

        # Execute query
        total_count = query.scalar()

        return total_count or 0

    except Exception as e:
        print(f"Error fetching feedback count: {e}")
        return 0


def resolve_all_feedback_by_image(image_id: int):
    try:
        # Get all guesses associated with the image
        guess_ids = (
            db.session.query(UserGuesses.guess_id)
            .filter(UserGuesses.image_id == image_id)
            .all()
        )

        guess_ids = [g[0] for g in guess_ids]

        if not guess_ids:
            return {"error": "No guesses found for the given image_id"}

        # Update feedback as resolved
        db.session.query(Feedback).filter(
            Feedback.feedback_id.in_(
                db.session.query(FeedbackUsers.feedback_id)
                .filter(FeedbackUsers.guess_id.in_(guess_ids))
                .subquery()
            )
        ).update({Feedback.resolved: True}, synchronize_session=False)

        db.session.commit()
        return {"message": "All feedback for the image has been marked as resolved"}

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}
