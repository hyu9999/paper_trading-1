from app.services.quotes.jq import JQQuotes
from app.services.quotes.tdx import TDXQuotes

quotes_mapping = {
    "JQDATA": JQQuotes,
    "TDX": TDXQuotes,
}
