from abc import ABC, abstractmethod


class BaseCategory(ABC):
    _registered_categories = []
    _registry = {}

    def __init__(self):
        BaseCategory._registered_categories.append(self)
        BaseCategory._registry[self.name] = self.__class__
        self.keywords = self.generate_keywords()

    @property
    @abstractmethod
    def name(self):
        """Get the name of the category."""
        raise NotImplementedError("Subclasses should implement this method.")

    @property
    @abstractmethod
    def icon(self):
        """Get the icon for the category."""
        raise NotImplementedError("Subclasses should implement this method.")

    @property
    @abstractmethod
    def color(self):
        """Get the color for the category."""
        raise NotImplementedError("Subclasses should implement this method.")

    @property
    def is_income(self):
        """Whether this category represents income. Override in income categories."""
        return False

    @property
    def is_expense(self):
        """Whether this category represents an expense. Override in income categories."""
        return True

    @abstractmethod
    def generate_keywords(self):
        """Generate keywords for the category."""
        raise NotImplementedError("Subclasses should implement this method.")

    @classmethod
    def get_registered_categories(cls):
        """Returns all registered category instances."""
        return cls._registered_categories

    @classmethod
    def get_registry(cls):
        return dict(cls._registry)


class TravelCategory(BaseCategory):
    @property
    def name(self):
        return "Travel"

    @property
    def icon(self):
        return "✈️"

    @property
    def color(self):
        return "blue"

    def generate_keywords(self):
        air_travel = [
            "travel",
            "airline",
            "flight",
            "airport",
            "baggage",
            "boarding",
            "passport",
            "visa",
            "customs",
            "immigration",
            "duty-free",
            "travel insurance",
            "trip insurance",
            "mobile boarding pass",
            "e-ticket",
            # Airlines
            "delta",
            "american airlines",
            "united airlines",
            "southwest airlines",
            "alaska airlines",
            "jetblue",
            "spirit airlines",
            "frontier airlines",
            "hawaiian airlines",
            "allegiant air",
            "sun country airlines",
            "air canada",
            "westjet",
            "british airways",
            "lufthansa",
            "air france",
            "klm",
            "qantas",
            "emirates",
            "etihad",
            "qatar airways",
            "turkish airlines",
            "singapore airlines",
            "cathay pacific",
            "japan airlines",
            "ana",
            "eva air",
            "korean air",
            "thai airways",
            "malaysia airlines",
            "air india",
            "indigo",
            "vistara",
            "saudi arabian airlines",
            "egyptair",
            "south african airways",
            "latam airlines",
            "gol airlines",
            "avianca",
            "copa airlines",
            "aeromexico",
            "aerolineas argentinas",
            "air new zealand",
        ]

        stays = [
            "hotel",
            "hostel",
            "resort",
            "motel",
            "inn",
            "lodge",
            "airbnb",
            "vrbo",
            "cabin",
            "chalet",
            "camping",
            "timeshare",
            "package deal",
            "airbnb experiences",
        ]

        ground_transport = [
            "metro",
            "metra",
            "train",
            "bus",
            "ferry",
            "cruise",
            "rental",
            "car hire",
            "taxi",
            "uber",
            "lyft",
            "shuttle",
            "bike rental",
            "scooter rental",
            "road trip",
            "rideshare",
        ]

        tours_experiences = [
            "tour",
            "sightseeing",
            "excursion",
            "adventure",
            "itinerary",
            "guided tour",
        ]

        outdoors = [
            "outdoors",
            "hiking",
            "mountaineering",
            "backpacking",
            "trekking",
            "yacht",
            "marina",
            "sailing",
            "diving",
            "snorkeling",
            "fishing",
            "kayak",
            "canoe",
        ]

        attractions = [
            "museum",
            "national park",
            "safari",
            "theme park",
            "zoo",
            "aquarium",
            "sightseeing pass",
        ]

        misc_travel = [
            "global entry",
            "tsa precheck",
            "booking",
            "expedia",
            "tripadvisor",
            "priceline",
            "skyscanner",
            "travel agency",
            "luggage",
        ]

        keywords = (
            air_travel
            + stays
            + ground_transport
            + tours_experiences
            + outdoors
            + attractions
            + misc_travel
        )
        return keywords


class ShoppingCategory(BaseCategory):
    @property
    def name(self):
        return "Shopping"

    @property
    def icon(self):
        return "🛍️"

    @property
    def color(self):
        return "purple"

    def generate_keywords(self):
        physical_stores = [
            "shopping",
            "mall",
            "department store",
            "convenience store",
            "target",
            "walmart",
            "home depot",
            "lowes",
        ]

        keywords = physical_stores
        return keywords


class OnlineShopping(BaseCategory):
    @property
    def name(self):
        return "Online Shopping"

    @property
    def icon(self):
        return "🛒"

    @property
    def color(self):
        return "orange"

    def generate_keywords(self):
        online_stores = [
            "online shopping",
            ".com",
            "amazon",
            "ebay",
            "alibaba",
            "etsy",
            "shopify",
        ]

        keywords = online_stores
        return keywords


class GroceriesCategory(BaseCategory):
    @property
    def name(self):
        return "Groceries"

    @property
    def icon(self):
        return "🥬"

    @property
    def color(self):
        return "green"

    def generate_keywords(self):
        groceries = [
            "groceries",
            "grocery store",
            "supermarket",
            "farmers market",
        ]

        grocery_stores = [
            "whole foods",
            "trader joe's",
            "costco",
            "safeway",
            "kroger",
            "aldi",
            "walmart",
            "target",
            "publix",
            "meijer",
            "market",
        ]

        keywords = groceries + grocery_stores
        return keywords


class EntertainmentCategory(BaseCategory):
    @property
    def name(self):
        return "Entertainment"

    @property
    def icon(self):
        return "🎬"

    @property
    def color(self):
        return "red"

    def generate_keywords(self):
        entertainment = [
            "cinemarksports basement",
            "sports",
            "game",
            "movie",
            "concert",
            "theater",
            "show",
            "event",
            "amusement park",
            "arcade",
            "bowling",
            "club",
            "bar",
        ]

        return entertainment


class UtilitiesCategory(BaseCategory):
    @property
    def name(self):
        return "Utilities"

    @property
    def icon(self):
        return "⚡"

    @property
    def color(self):
        return "yellow"

    def generate_keywords(self):
        utilities = [
            "electricity",
            "water",
            "gas",
            "internet",
            "phone",
            "cable",
            "trash",
            "sewer",
            "pg&e",
            "pge&e",
            "power",
            "utility",
        ]

        return utilities


class HousingCategory(BaseCategory):
    @property
    def name(self):
        return "Housing"

    @property
    def icon(self):
        return "🏠"

    @property
    def color(self):
        return "brown"

    def generate_keywords(self):
        housing = [
            "rent",
            "mortgage",
            "property tax",
            "home insurance",
            "hoa fee",
            "maintenance",
            "repair",
            "renovation",
            "apartment",
            "condo",
            "townhouse",
            "homeowners",
            "ikea",
        ]

        return housing


class MedicalCategory(BaseCategory):
    @property
    def name(self):
        return "Medical"

    @property
    def icon(self):
        return "🏥"

    @property
    def color(self):
        return "pink"

    def generate_keywords(self):
        medical = [
            "doctor",
            "clinic",
            "pharmacy",
            "prescription",
            "medical bill",
            "health insurance",
            "dental",
            "vision",
            "wellness",
        ]

        return medical


class EducationCategory(BaseCategory):
    @property
    def name(self):
        return "Education"

    @property
    def icon(self):
        return "📚"

    @property
    def color(self):
        return "blue"

    def generate_keywords(self):
        education = [
            "tuition",
            "school",
            "college",
            "university",
            "textbook",
            "course",
            "class",
            "workshop",
            "seminar",
            "training",
        ]

        return education


class SavingsCategory(BaseCategory):
    @property
    def name(self):
        return "Savings"

    @property
    def icon(self):
        return "💰"

    @property
    def color(self):
        return "green"

    def generate_keywords(self):
        savings = [
            "savings account",
            "high-yield savings",
            "certificate of deposit",
            "money market",
            "IRA",
            "401(k)",
            "investment account",
        ]

        return savings


class GiftsCategory(BaseCategory):
    @property
    def name(self):
        return "Gifts"

    @property
    def icon(self):
        return "🎁"

    @property
    def color(self):
        return "purple"

    def generate_keywords(self):
        gifts = [
            "gift",
            "present",
            "donation",
        ]

        return gifts


class DiningCategory(BaseCategory):
    @property
    def name(self):
        return "Dining"

    @property
    def icon(self):
        return "🍽️"

    @property
    def color(self):
        return "red"

    def generate_keywords(self):
        restaurants = [
            "restaurant",
            "cafe",
            "diner",
            "takeout",
            "delivery",
            "food truck",
            "catering",
            "meal kit",
            "olive garden",
            "red lobster",
            "cheesecake factory",
            "outback steakhouse",
            "applebee's",
            "chili's",
            "buffalo wild wings",
            "ihop",
            "denny's",
            "waffle house",
            "bbq",
        ]

        fast_food = [
            "mcdonald's",
            "burger king",
            "subway",
            "taco bell",
            "pizza hut",
            "domino's",
            "chipotle",
            "panda express",
        ]

        other_food = [
            "food",
            "food & drink",
            "uber eats",
            "doordash",
            "grubhub",
            "postmates",
            "panera bread",
            "meal kit",
        ]

        drinks = [
            "drink",
            "bar",
            "starbucks",
            "dunkin'",
            "boba",
            "bubble tea",
            "smoothie",
            "juice bar",
        ]
        keywords = restaurants + fast_food + other_food + drinks
        return keywords


class InvestmentsCategory(BaseCategory):
    @property
    def name(self):
        return "Investments"

    @property
    def icon(self):
        return "📈"

    @property
    def color(self):
        return "orange"

    def generate_keywords(self):
        investments = [
            "stocks",
            "bonds",
            "mutual funds",
            "ETFs",
            "real estate",
            "cryptocurrency",
            "investment account",
            "brokerage account",
            "retirement account",
        ]

        keywords = investments
        return keywords


class SubscriptionsCategory(BaseCategory):
    @property
    def name(self):
        return "Subscriptions"

    @property
    def icon(self):
        return "📱"

    @property
    def color(self):
        return "purple"

    def generate_keywords(self):
        subscriptions = [
            "subscription",
            "membership",
            "monthly fee",
            "annual fee",
            "recurring payment",
            "streaming service",
            "netflix",
            "hulu",
            "spotify",
            "apple music",
            "amazon prime",
            "disney+",
            "hbo max",
            "youtube premium",
            "audible",
            "siriusxm",
            "pandora",
            "twitch",
            "patreon",
            "onlyfans",
            "plaid",
            "openai",
            "chatgpt",
        ]

        keywords = subscriptions
        return keywords


class CharityCategory(BaseCategory):
    @property
    def name(self):
        return "Charity"

    @property
    def icon(self):
        return "❤️"

    @property
    def color(self):
        return "pink"

    def generate_keywords(self):
        charity = [
            "donation",
            "charity",
            "nonprofit",
            "fundraiser",
            "crowdfunding",
            "go fund me",
            "kickstarter",
            "indiegogo",
            "charitable contribution",
            "tax-deductible donation",
        ]

        keywords = charity
        return keywords


class PetCategory(BaseCategory):
    @property
    def name(self):
        return "Pet"

    @property
    def icon(self):
        return "🐾"

    @property
    def color(self):
        return "brown"

    def generate_keywords(self):
        pet = [
            "pet",
            "dog",
            "cat",
            "vet",
            "petco",
            "petsmart",
            "chewy",
            "barkbox",
            "pet insurance",
            "pet food",
            "pet supplies",
            "pet insurance",
            "dog walking",
            "pet sitting",
        ]

        keywords = pet
        return keywords


class WholesaleCategory(BaseCategory):
    @property
    def name(self):
        return "Wholesale"

    @property
    def icon(self):
        return "📦"

    @property
    def color(self):
        return "green"

    def generate_keywords(self):
        wholesale = [
            "wholesale",
            "costco",
            "sam's club",
        ]

        keywords = wholesale
        return keywords


class CardCategory(BaseCategory):
    @property
    def name(self):
        return "Car"

    @property
    def icon(self):
        return "🚗"

    @property
    def color(self):
        return "blue"

    def generate_keywords(self):
        car = [
            "car payment",
            "car insurance",
            "gas",
            "fuel",
            "maintenance",
            "repair",
            "tire",
            "brake",
            "oil change",
            "car wash",
            "parking",
            "toll",
            "roadside assistance",
        ]

        keywords = car
        return keywords


class PhoneCategory(BaseCategory):
    @property
    def name(self):
        return "Phone"

    @property
    def icon(self):
        return "📞"

    @property
    def color(self):
        return "yellow"

    def generate_keywords(self):
        phone = [
            "phone bill",
            "cell phone",
            "mobile plan",
            "at&t",
            "verizon",
            "t-mobile",
            "sprint",
            "boost mobile",
            "cricket",
            "metro by t-mobile",
            "tmobile",
        ]

        keywords = phone
        return keywords


class MiscellaneousCategory(BaseCategory):
    @property
    def name(self):
        return "Miscellaneous"

    @property
    def icon(self):
        return "🔧"

    @property
    def color(self):
        return "gray"

    def generate_keywords(self):
        miscellaneous = [
            "miscellaneous",
            "other",
        ]

        keywords = miscellaneous
        return keywords


class PaymentsCategory(BaseCategory):
    @property
    def name(self):
        return "Payments"

    @property
    def icon(self):
        return "💳"

    @property
    def color(self):
        return "orange"

    def generate_keywords(self):
        payments = [
            "mobile payment",
            "payment",
            "bill",
        ]

        return payments


class UnknownCategory(BaseCategory):
    @property
    def name(self):
        return "Unknown"

    @property
    def icon(self):
        return "❓"

    @property
    def color(self):
        return "gray"

    def generate_keywords(self):
        return []


# region Income Categories
class SalaryIncomeCategory(BaseCategory):
    """Salary and payroll income."""

    @property
    def name(self):
        return "Salary"

    @property
    def icon(self):
        return "💰"

    @property
    def color(self):
        return "green"

    @property
    def is_income(self):
        return True

    @property
    def is_expense(self):
        return False

    def generate_keywords(self):
        payroll = [
            "payroll",
            "direct deposit",
            "direct dep",
            "salary",
            "wages",
            "paycheck",
            "compensation",
            "net pay",
            "pay period",
        ]

        payroll_providers = [
            "adp",
            "gusto",
            "paychex",
            "workday",
            "paylocity",
            "paycom",
            "ceridian",
            "ultipro",
            "rippling",
            "justworks",
            "zenefits",
        ]

        return payroll + payroll_providers


class FreelanceIncomeCategory(BaseCategory):
    """Freelance and self-employment income."""

    @property
    def name(self):
        return "Freelance Income"

    @property
    def icon(self):
        return "💼"

    @property
    def color(self):
        return "teal"

    @property
    def is_income(self):
        return True

    @property
    def is_expense(self):
        return False

    def generate_keywords(self):
        freelance = [
            "freelance",
            "contractor",
            "consulting",
            "1099",
            "self-employment",
            "client payment",
            "invoice payment",
        ]

        platforms = [
            "upwork",
            "fiverr",
            "toptal",
            "freelancer",
        ]

        return freelance + platforms


class InterestIncomeCategory(BaseCategory):
    """Interest income from savings and bank accounts."""

    @property
    def name(self):
        return "Interest Income"

    @property
    def icon(self):
        return "🏦"

    @property
    def color(self):
        return "blue"

    @property
    def is_income(self):
        return True

    @property
    def is_expense(self):
        return False

    def generate_keywords(self):
        interest = [
            "interest payment",
            "interest earned",
            "interest credit",
            "apy interest",
            "savings interest",
            "interest paid",
            "interest income",
            "accrued interest",
        ]

        return interest


class DividendIncomeCategory(BaseCategory):
    """Dividend income from investments."""

    @property
    def name(self):
        return "Dividend Income"

    @property
    def icon(self):
        return "📊"

    @property
    def color(self):
        return "purple"

    @property
    def is_income(self):
        return True

    @property
    def is_expense(self):
        return False

    def generate_keywords(self):
        dividends = [
            "dividend",
            "div payment",
            "quarterly dividend",
            "stock dividend",
            "fund distribution",
            "capital gain dist",
            "reinvested dividend",
        ]

        return dividends


class RefundCategory(BaseCategory):
    """Refunds and returns."""

    @property
    def name(self):
        return "Refund"

    @property
    def icon(self):
        return "↩️"

    @property
    def color(self):
        return "orange"

    @property
    def is_income(self):
        return False  # Refunds are NOT income, they're expense reversals

    @property
    def is_expense(self):
        return False  # Also not an expense

    def generate_keywords(self):
        refunds = [
            "refund",
            "return",
            "credit adjustment",
            "reversal",
            "reimbursement",
            "chargeback",
            "cashback",
            "cash back",
            "rebate",
        ]

        return refunds


class TaxRefundCategory(BaseCategory):
    """Tax refunds from government."""

    @property
    def name(self):
        return "Tax Refund"

    @property
    def icon(self):
        return "🏛️"

    @property
    def color(self):
        return "green"

    @property
    def is_income(self):
        return True

    @property
    def is_expense(self):
        return False

    def generate_keywords(self):
        tax_refunds = [
            "irs treas",
            "tax refund",
            "state tax refund",
            "federal tax refund",
            "tax ref",
            "treasury",
            "irs",
        ]

        return tax_refunds


class TransferCategory(BaseCategory):
    """Internal transfers between accounts - neither income nor expense."""

    @property
    def name(self):
        return "Transfer"

    @property
    def icon(self):
        return "🔄"

    @property
    def color(self):
        return "gray"

    @property
    def is_income(self):
        return False  # Transfers are not income

    @property
    def is_expense(self):
        return False  # Transfers are not expenses

    def generate_keywords(self):
        transfers = [
            "transfer",
            "xfer",
            "internal transfer",
            "account transfer",
            "wire transfer",
            "ach transfer",
            "online transfer",
            "bank transfer",
        ]

        peer_to_peer = [
            "zelle",
            "venmo",
            "cash app",
            "paypal",
            "apple cash",
        ]

        return transfers + peer_to_peer


class CreditCardPaymentCategory(BaseCategory):
    """Credit card payments - not an expense (paying off debt)."""

    @property
    def name(self):
        return "Credit Card Payment"

    @property
    def icon(self):
        return "💳"

    @property
    def color(self):
        return "slate"

    @property
    def is_income(self):
        return False

    @property
    def is_expense(self):
        return False  # Paying off credit card is not an expense

    def generate_keywords(self):
        payments = [
            "payment thank you",
            "autopay",
            "auto pay",
            "credit card payment",
            "card payment",
            "online payment",
            "payment received",
            "payment - thank",
        ]

        return payments


# endregion Income Categories


# region Register Categories
def register_categories():
    """Register all available categories."""
    # Expense categories
    TravelCategory()
    ShoppingCategory()
    OnlineShopping()
    GroceriesCategory()
    EntertainmentCategory()
    UtilitiesCategory()
    HousingCategory()
    MedicalCategory()
    EducationCategory()
    SavingsCategory()
    GiftsCategory()
    DiningCategory()
    InvestmentsCategory()
    SubscriptionsCategory()
    CharityCategory()
    PetCategory()
    WholesaleCategory()
    CardCategory()
    PhoneCategory()
    MiscellaneousCategory()
    PaymentsCategory()
    UnknownCategory()

    # Income categories
    SalaryIncomeCategory()
    FreelanceIncomeCategory()
    InterestIncomeCategory()
    DividendIncomeCategory()
    TaxRefundCategory()

    # Neither income nor expense (transfers, refunds)
    RefundCategory()
    TransferCategory()
    CreditCardPaymentCategory()


register_categories()
# endregion Register Categories
