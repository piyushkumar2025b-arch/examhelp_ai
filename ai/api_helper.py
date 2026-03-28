from utils.query_engine import QueryEngine
from utils.app_controller import AppController
from utils.web_handler import scrape_web_page

class APIHelper:
    @staticmethod
    def search_web(query, max_res=3):
        return QueryEngine.search_duckduckgo(query, max_res)

    @staticmethod
    def get_wikipedia(query):
        return QueryEngine.search_wikipedia(query)

    @staticmethod
    def fetch_web_content(url):
        text, title = scrape_web_page(url)
        return {"title": title, "text": text}

    @staticmethod
    def evaluate_math(expr):
        return AppController.evaluate_expression(expr)
