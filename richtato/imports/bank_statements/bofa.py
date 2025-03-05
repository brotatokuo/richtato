from core import BankImporter


class BankOfAmerica(BankImporter):
    def __init__(self, df):
        super().__init__(df)

    @property
    def name(self):
        return "Bank of America"

    def _compute_description_column(self):
        return self.df["Description"]

    def _compute_date_column(self):
        return self.df["Date"]

    def _compute_amount_column(self):
        return self.df["Debit Amount"].fillna(self.df["Credit Amount"])
