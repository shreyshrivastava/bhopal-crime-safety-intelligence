"""No person-level wanted registry is published without record-specific verification."""
def get_verified_public_records():
    return {
        'records': [], 'total_records': 0,
        'disclaimer': 'No person-level public records have been independently verified for this portal.',
        'source_authority': None, 'primary_url': 'https://bhopal.mppolice.gov.in/',
        'last_audit_date': None, 'compliance_notes': [],
    }
