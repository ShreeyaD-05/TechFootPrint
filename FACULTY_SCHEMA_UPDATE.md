# Faculty Schema Improvements — Migration 010

## Overview
This migration adds comprehensive fields to properly maintain faculty profiles, college metadata, and faculty-student assignment integrity.

## Database Changes

### `users` table — New Columns
| Column | Type | Purpose |
|--------|------|---------|
| `phone` | VARCHAR(20) | Contact number (faculty & students) |
| `employee_id` | VARCHAR(50) | Faculty employee/staff ID (unique per college) |
| `joining_date` | DATE | When faculty joined the institution |
| `specialization` | VARCHAR(200) | Faculty area of expertise / subject |
| `is_first_login` | BOOLEAN | Flag to force password change on first login (default: TRUE) |

**New Index:** `ix_users_college_role` on `(college_id, role)` — fast lookup of all faculty/students in a college

### `colleges` table — New Columns
| Column | Type | Purpose |
|--------|------|---------|
| `contact_email` | VARCHAR(255) | Primary contact email for the college |
| `contact_phone` | VARCHAR(20) | Primary contact phone |
| `website` | VARCHAR(500) | College website URL |
| `established_year` | INTEGER | Year the college was established |

**New Index:** `ix_colleges_is_active` on `is_active` — fast filtering of active colleges

### `mentor_assignments` table — New Columns
| Column | Type | Purpose |
|--------|------|---------|
| `notes` | TEXT | Reason / context for the assignment |
| `unassigned_at` | DATETIME | When the assignment was deactivated |

**New Index:** `ix_mentor_assignments_active` on `(student_id, is_active)` — fast active-assignment lookup

**New Constraint:** `uq_mentor_assignments_one_active_per_student` — **UNIQUE** partial index on `student_id` WHERE `is_active = TRUE`
- **Enforces one active mentor per student at the database level**
- Prevents race conditions and duplicate assignments
- PostgreSQL-specific (uses WHERE clause on unique index)

## API Changes

### Updated Schemas

**`CollegeCreate` / `CollegeUpdate` / `CollegeResponse`:**
- Added: `contact_email`, `contact_phone`, `website`, `established_year`

**`FacultyCreate` / `FacultyUpdate` / `FacultyResponse`:**
- Added: `phone`, `employee_id`, `joining_date`, `specialization`

**`UserCreateByAdmin` / `UserUpdateByAdmin` / `UserWithRoleResponse`:**
- Added: `phone`, `employee_id`, `joining_date`, `specialization`, `is_first_login`

**`MentorAssignmentCreate` / `MentorAssignmentResponse`:**
- Added: `notes`, `unassigned_at`

### Behavioral Changes

**Password Change (`POST /auth/change-password`):**
- Now clears `is_first_login` flag after successful password change
- Allows tracking which users have changed their temp password

**Faculty Deactivation (`DELETE /admin/faculty/{id}`):**
- Now automatically deactivates all active mentor assignments for that faculty
- Sets `unassigned_at` timestamp on deactivated assignments

**Student Assignment (`POST /faculty/students/{id}/assign-faculty`):**
- Sets `unassigned_at` when deactivating old assignments
- Database constraint prevents duplicate active assignments

**Bulk Assignment (`POST /faculty/students/bulk-assign-faculty`):**
- Sets `unassigned_at` when replacing assignments

## Migration Instructions

```bash
# Navigate to backend directory
cd backend

# Run the migration
alembic upgrade head

# Verify migration applied
alembic current
# Should show: 010_faculty_schema_improvements (head)
```

## Rollback (if needed)

```bash
alembic downgrade 009_add_chat_messages
```

## Frontend Impact

**No breaking changes** — all new fields are optional. Existing forms will continue to work.

**Optional enhancements:**
- Add phone/employee_id/joining_date/specialization fields to faculty create/edit forms
- Add contact_email/contact_phone/website/established_year to college create/edit forms
- Display `is_first_login` badge on user lists to identify users who haven't changed their temp password
- Show `unassigned_at` in assignment history views

## Data Integrity Benefits

1. **Unique constraint** prevents duplicate active assignments (was previously only enforced in application code)
2. **Audit trail** via `unassigned_at` — know when assignments were removed
3. **Faculty metadata** enables better reporting and contact management
4. **College metadata** enables richer college profiles and external integrations
5. **First-login tracking** helps identify users who need to change their temp password

## Notes

- All new columns are **nullable** — existing data is unaffected
- The unique constraint uses a **partial index** (PostgreSQL-specific) — only enforces uniqueness where `is_active = TRUE`
- `joining_date` is stored as `DATE` (not `DATETIME`) — only year/month/day, no time component
- `is_first_login` defaults to `TRUE` for all new users — cleared on first password change
