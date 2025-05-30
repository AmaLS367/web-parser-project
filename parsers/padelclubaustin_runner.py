#parsers.padelclubaustin_runner
from .padelclubaustin_parser import PadelClubAustinParser

def run_once():
    parser = PadelClubAustinParser()
    return parser.run_once()
