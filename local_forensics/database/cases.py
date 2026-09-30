from .repository import SupabaseRepository

class CaseManager:
    # The frontend does not use a separate `cases` table.
    # A report row in vda_transaction_logs is the investigation case.
    def __init__(self):
        self.repo = SupabaseRepository()

    def get_cases(self, limit=100):
        return self.repo.get_transaction_logs(limit)

    def get_case(self, case_id):
        return self.repo.get_transaction_log(case_id)
