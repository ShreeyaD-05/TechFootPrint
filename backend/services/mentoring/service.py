from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime
from shared.models import (
    User, MentorAssignment, MentorFeedback, CodingGoal, 
    ProblemNote, Analytics, ProblemStats, PlatformAccount
)
from shared.schemas import (
    MentorAssignmentCreate, MentorFeedbackCreate, 
    CodingGoalCreate, ProblemNoteCreate, StudentProgressSummary
)

class MentoringService:
    @staticmethod
    def assign_mentor(db: Session, assignment: MentorAssignmentCreate, assigned_by_id: int) -> MentorAssignment:
        """Assign a mentor to a student"""
        # Check if assignment already exists
        existing = db.query(MentorAssignment).filter(
            and_(
                MentorAssignment.mentor_id == assignment.mentor_id,
                MentorAssignment.student_id == assignment.student_id,
                MentorAssignment.is_active == True
            )
        ).first()
        
        if existing:
            return existing
        
        db_assignment = MentorAssignment(
            mentor_id=assignment.mentor_id,
            student_id=assignment.student_id,
            assigned_by=assigned_by_id
        )
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        return db_assignment
    
    @staticmethod
    def get_mentor_students(db: Session, mentor_id: int) -> List[User]:
        """Get all students assigned to a mentor"""
        assignments = db.query(MentorAssignment).filter(
            and_(
                MentorAssignment.mentor_id == mentor_id,
                MentorAssignment.is_active == True
            )
        ).all()
        
        student_ids = [a.student_id for a in assignments]
        students = db.query(User).filter(User.id.in_(student_ids)).all()
        return students
    
    @staticmethod
    def get_student_mentor(db: Session, student_id: int) -> Optional[User]:
        """Get the mentor assigned to a student"""
        assignment = db.query(MentorAssignment).filter(
            and_(
                MentorAssignment.student_id == student_id,
                MentorAssignment.is_active == True
            )
        ).first()
        
        if assignment:
            return db.query(User).filter(User.id == assignment.mentor_id).first()
        return None
    
    @staticmethod
    def create_feedback(db: Session, mentor_id: int, feedback: MentorFeedbackCreate) -> MentorFeedback:
        """Create mentor feedback for a student"""
        db_feedback = MentorFeedback(
            mentor_id=mentor_id,
            student_id=feedback.student_id,
            feedback_type=feedback.feedback_type,
            title=feedback.title,
            content=feedback.content,
            priority=feedback.priority
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return db_feedback
    
    @staticmethod
    def get_student_feedback(db: Session, student_id: int, unread_only: bool = False) -> List[MentorFeedback]:
        """Get all feedback for a student"""
        query = db.query(MentorFeedback).filter(MentorFeedback.student_id == student_id)
        if unread_only:
            query = query.filter(MentorFeedback.is_read == False)
        return query.order_by(MentorFeedback.created_at.desc()).all()
    
    @staticmethod
    def mark_feedback_read(db: Session, feedback_id: int) -> MentorFeedback:
        """Mark feedback as read"""
        feedback = db.query(MentorFeedback).filter(MentorFeedback.id == feedback_id).first()
        if feedback:
            feedback.is_read = True
            db.commit()
            db.refresh(feedback)
        return feedback
    
    @staticmethod
    def create_goal(db: Session, created_by_id: int, goal: CodingGoalCreate) -> CodingGoal:
        """Create a coding goal"""
        db_goal = CodingGoal(
            created_by=created_by_id,
            target_type=goal.target_type,
            target_id=goal.target_id,
            batch_year=goal.batch_year,
            department=goal.department,
            goal_type=goal.goal_type,
            target_value=goal.target_value,
            deadline=goal.deadline,
            description=goal.description
        )
        db.add(db_goal)
        db.commit()
        db.refresh(db_goal)
        return db_goal
    
    @staticmethod
    def get_student_goals(db: Session, student_id: int) -> List[CodingGoal]:
        """Get goals for a student (individual + batch + department)"""
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            return []
        
        goals = db.query(CodingGoal).filter(
            and_(
                CodingGoal.is_active == True,
                (
                    (CodingGoal.target_id == student_id) |
                    (and_(CodingGoal.target_type == "batch", CodingGoal.batch_year == student.batch_year)) |
                    (and_(CodingGoal.target_type == "department", CodingGoal.department == student.department))
                )
            )
        ).all()
        return goals
    
    @staticmethod
    def create_problem_note(db: Session, user_id: int, note: ProblemNoteCreate) -> ProblemNote:
        """Create a note for a problem"""
        db_note = ProblemNote(
            user_id=user_id,
            problem_stat_id=note.problem_stat_id,
            note_content=note.note_content,
            tags=note.tags
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note
    
    @staticmethod
    def get_problem_notes(db: Session, user_id: int, problem_stat_id: Optional[int] = None) -> List[ProblemNote]:
        """Get notes for problems"""
        query = db.query(ProblemNote).filter(ProblemNote.user_id == user_id)
        if problem_stat_id:
            query = query.filter(ProblemNote.problem_stat_id == problem_stat_id)
        return query.order_by(ProblemNote.updated_at.desc()).all()
    
    @staticmethod
    def get_student_progress_summary(db: Session, student_id: int) -> dict:
        """Get comprehensive progress summary for a student"""
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            return None
        
        analytics = db.query(Analytics).filter(Analytics.user_id == student_id).first()
        feedback_count = db.query(func.count(MentorFeedback.id)).filter(
            MentorFeedback.student_id == student_id
        ).scalar()
        
        last_activity = db.query(func.max(ProblemStats.solved_at)).filter(
            ProblemStats.platform_account_id.in_(
                db.query(PlatformAccount.id).filter(PlatformAccount.user_id == student_id)
            )
        ).scalar()
        
        return {
            "user_id": student.id,
            "username": student.username,
            "full_name": student.full_name,
            "batch_year": student.batch_year,
            "department": student.department,
            "total_problems": analytics.total_problems_solved if analytics else 0,
            "current_streak": analytics.current_streak if analytics else 0,
            "last_active": last_activity,
            "mentor_feedback_count": feedback_count
        }
